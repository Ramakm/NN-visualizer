// Draggable Panels Functionality
// Makes the left panel and right prediction panel draggable

(function() {
  'use strict';
  
  function makeDraggable(element) {
    if (!element) return;
    
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    let xOffset = 0;
    let yOffset = 0;
    
    // Get the container (the draggable part)
    const container = element.querySelector('.container') || element;
    
    // Add draggable cursor
    container.style.cursor = 'grab';
    
    // Add header for better drag handle (optional)
    const header = container.querySelector('h3, .grid-title');
    if (header) {
      header.style.cursor = 'grab';
      header.style.userSelect = 'none';
    }
    
    function dragStart(e) {
      // Only allow dragging from header or container, not from interactive elements
      const target = e.target;
      if (target.tagName === 'BUTTON' || 
          target.tagName === 'INPUT' || 
          target.closest('button') ||
          target.closest('input') ||
          target.classList.contains('grid') ||
          target.classList.contains('grid-cell') ||
          target.classList.contains('digit-button')) {
        return;
      }
      
      if (e.type === 'touchstart') {
        initialX = e.touches[0].clientX - xOffset;
        initialY = e.touches[0].clientY - yOffset;
      } else {
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;
      }
      
      isDragging = true;
      element.classList.add('dragging');
      container.style.cursor = 'grabbing';
      if (header) header.style.cursor = 'grabbing';
    }
    
    function dragEnd(e) {
      if (!isDragging) return;
      
      isDragging = false;
      element.classList.remove('dragging');
      container.style.cursor = 'grab';
      if (header) header.style.cursor = 'grab';
      
      // Save position
      xOffset = currentX;
      yOffset = currentY;
    }
    
    function drag(e) {
      if (!isDragging) return;
      
      e.preventDefault();
      
      if (e.type === 'touchmove') {
        currentX = e.touches[0].clientX - initialX;
        currentY = e.touches[0].clientY - initialY;
      } else {
        currentX = e.clientX - initialX;
        currentY = e.clientY - initialY;
      }
      
      xOffset = currentX;
      yOffset = currentY;
      
      setTranslate(currentX, currentY, element);
    }
    
    function setTranslate(xPos, yPos, el) {
      const currentTransform = el.style.transform;
      
      // Preserve any existing transforms (like translateX(-50%) for centering)
      if (currentTransform && currentTransform.includes('translateX(-50%)')) {
        el.style.transform = `translateX(-50%) translate(${xPos}px, ${yPos}px)`;
      } else if (currentTransform && currentTransform.includes('translateX(50%)')) {
        el.style.transform = `translateX(50%) translate(${xPos}px, ${yPos}px)`;
      } else {
        el.style.transform = `translate(${xPos}px, ${yPos}px)`;
      }
    }
    
    // Mouse events
    container.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);
    
    // Touch events
    container.addEventListener('touchstart', dragStart, { passive: false });
    document.addEventListener('touchmove', drag, { passive: false });
    document.addEventListener('touchend', dragEnd);
  }
  
  // Initialize draggable panels when DOM is loaded
  function initDraggable() {
    const leftPanel = document.getElementById('overlay2d');
    const rightPanel = document.getElementById('predictionOverlay');
    
    if (leftPanel) {
      makeDraggable(leftPanel);
      leftPanel.classList.add('draggable');
    }
    
    if (rightPanel) {
      makeDraggable(rightPanel);
      rightPanel.classList.add('draggable');
    }
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDraggable);
  } else {
    initDraggable();
  }
})();
