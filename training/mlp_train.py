"""
Training script for MNIST MLP with export functionality.
Supports Apple Metal (MPS), CUDA, and CPU acceleration.
"""

import argparse
import json
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# MNIST normalization constants
MNIST_MEAN = 0.1307
MNIST_STD = 0.3081


def get_device(preferred=None):
    """Get the best available device for training."""
    if preferred:
        if preferred == "mps" and torch.backends.mps.is_available():
            return torch.device("mps")
        elif preferred == "cuda" and torch.cuda.is_available():
            return torch.device("cuda")
        elif preferred == "cpu":
            return torch.device("cpu")
    
    # Auto-detect best device
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


class SimpleMLP(nn.Module):
    """Simple Multi-Layer Perceptron for MNIST classification."""
    
    def __init__(self, input_dim=784, hidden_dims=(64, 32), num_classes=10):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        # Hidden layers with ReLU activation
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(prev_dim, num_classes))
        
        self.network = nn.Sequential(*layers)
        self.hidden_dims = hidden_dims
    
    def forward(self, x):
        x = x.view(x.size(0), -1)  # Flatten
        return self.network(x)


def train_epoch(model, train_loader, optimizer, criterion, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        pred = output.argmax(dim=1)
        correct += (pred == target).sum().item()
        total += target.size(0)
        
        if (batch_idx + 1) % 100 == 0:
            print(f"  Batch {batch_idx + 1}/{len(train_loader)} | "
                  f"Loss: {loss.item():.4f} | "
                  f"Acc: {100 * correct / total:.2f}%")
    
    avg_loss = total_loss / len(train_loader)
    accuracy = correct / total
    return avg_loss, accuracy


def evaluate(model, test_loader, criterion, device):
    """Evaluate on test set."""
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = criterion(output, target)
            
            total_loss += loss.item()
            pred = output.argmax(dim=1)
            correct += (pred == target).sum().item()
            total += target.size(0)
    
    avg_loss = total_loss / len(test_loader)
    accuracy = correct / total
    return avg_loss, accuracy


def export_weights(model, output_path, hidden_dims):
    """Export model weights to JSON format for visualization."""
    model.eval()
    
    # Extract layers (skip ReLU layers)
    dense_layers = [m for m in model.network if isinstance(m, nn.Linear)]
    
    # Build layer metadata and weights
    layers = []
    for idx, layer in enumerate(dense_layers):
        # Determine activation
        if idx < len(dense_layers) - 1:
            activation = "relu"
        else:
            activation = "none"
        
        # Get weights and biases as numpy arrays
        weights = layer.weight.detach().cpu().numpy().tolist()
        bias = layer.bias.detach().cpu().numpy().tolist()
        
        layer_data = {
            "layer_index": idx,
            "type": "dense",
            "name": f"dense_{idx}",
            "activation": activation,
            "weight_shape": list(layer.weight.shape),
            "bias_shape": list(layer.bias.shape),
            "weights": weights,
            "bias": bias
        }
        
        layers.append(layer_data)
    
    # Build complete export structure
    export_data = {
        "version": 2,
        "dtype": "float32",
        "network": {
            "architecture": [784] + list(hidden_dims) + [10],
            "normalization": {
                "mean": MNIST_MEAN,
                "std": MNIST_STD
            },
            "layers": layers
        },
        "timeline": []  # Can be extended for training progress visualization
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✓ Weights exported to: {output_path}")
    print(f"  - Architecture: {export_data['network']['architecture']}")
    print(f"  - Total layers: {len(layers)}")


def main():
    parser = argparse.ArgumentParser(description="Train MNIST MLP and export for visualization")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=128, help="Batch size for training")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--hidden-dims", type=int, nargs="+", default=[64, 32], 
                        help="Hidden layer dimensions")
    parser.add_argument("--device", type=str, choices=["auto", "mps", "cuda", "cpu"], 
                        default="auto", help="Device to use for training")
    parser.add_argument("--export-path", type=str, default="exports/mlp_weights.json",
                        help="Path to export weights")
    parser.add_argument("--data-dir", type=str, default="./data",
                        help="Directory for MNIST dataset")
    
    args = parser.parse_args()
    
    # Setup device
    device = get_device(None if args.device == "auto" else args.device)
    print(f"\n🚀 Using device: {device}")
    
    # Prepare data
    print("\n📥 Loading MNIST dataset...")
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((MNIST_MEAN,), (MNIST_STD,))
    ])
    
    train_dataset = datasets.MNIST(args.data_dir, train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(args.data_dir, train=False, transform=transform)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)
    
    print(f"  - Training samples: {len(train_dataset)}")
    print(f"  - Test samples: {len(test_dataset)}")
    
    # Create model
    print(f"\n🏗️  Building model with architecture: 784 → {' → '.join(map(str, args.hidden_dims))} → 10")
    model = SimpleMLP(
        input_dim=784,
        hidden_dims=tuple(args.hidden_dims),
        num_classes=10
    ).to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  - Total parameters: {total_params:,}")
    
    # Setup training
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    
    # Training loop
    print(f"\n🎯 Training for {args.epochs} epochs...")
    best_accuracy = 0
    
    for epoch in range(1, args.epochs + 1):
        print(f"\nEpoch {epoch}/{args.epochs}")
        print("-" * 60)
        
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, device)
        test_loss, test_acc = evaluate(model, test_loader, criterion, device)
        
        print(f"\n  Train - Loss: {train_loss:.4f} | Accuracy: {train_acc * 100:.2f}%")
        print(f"  Test  - Loss: {test_loss:.4f} | Accuracy: {test_acc * 100:.2f}%")
        
        if test_acc > best_accuracy:
            best_accuracy = test_acc
            print(f"  ✨ New best accuracy: {best_accuracy * 100:.2f}%")
    
    # Export weights
    print(f"\n💾 Exporting model weights...")
    export_path = Path(args.export_path)
    export_weights(model, export_path, args.hidden_dims)
    
    print(f"\n✅ Training complete!")
    print(f"  - Best test accuracy: {best_accuracy * 100:.2f}%")
    print(f"  - Weights saved to: {export_path}")
    print(f"\n🎨 Ready to visualize! Start a web server and open index.html")


if __name__ == "__main__":
    main()
