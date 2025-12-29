/**
 * Vanilla JS Scramble Text Effect
 * Inspired by use-scramble library
 */

(function() {
  'use strict';

  // Check for reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Get random integer in range
  function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  // Get random character from unicode range
  function getRandomChar(range) {
    const rand = range.length === 2 
      ? getRandomInt(range[0], range[1])
      : range[getRandomInt(0, range.length - 1)];
    return String.fromCharCode(rand);
  }

  // Main scramble function
  function scrambleText(element, options) {
    if (!element) return;

    const defaults = {
      speed: 0.5,           // Animation speed (0-1)
      scramble: 5,          // Number of scramble iterations per character
      seed: 3,              // Characters to scramble ahead
      range: [65, 125],     // Unicode range for random chars (A-Z, a-z, symbols)
      overdrive: true,      // Continue scrambling at the end
    };

    const settings = { ...defaults, ...options };
    const originalText = element.getAttribute('data-scramble-text') || element.textContent;
    
    // Store original text if not already stored
    if (!element.getAttribute('data-scramble-text')) {
      element.setAttribute('data-scramble-text', originalText);
    }

    // Skip animation if user prefers reduced motion
    if (prefersReducedMotion) {
      element.textContent = originalText;
      return;
    }

    let currentIndex = 0;
    let scrambleArray = new Array(originalText.length).fill(null);
    let scrambleCounts = new Array(originalText.length).fill(0);
    let frameCount = 0;
    const fpsInterval = 1000 / (60 * settings.speed);
    let lastFrameTime = Date.now();
    let animationId = null;

    function animate() {
      const now = Date.now();
      const elapsed = now - lastFrameTime;

      if (elapsed > fpsInterval) {
        lastFrameTime = now - (elapsed % fpsInterval);
        frameCount++;

        // Update scramble array
        let result = '';
        let isComplete = true;

        for (let i = 0; i < originalText.length; i++) {
          if (originalText[i] === ' ') {
            result += ' ';
            continue;
          }

          if (scrambleArray[i] === null && i <= currentIndex + settings.seed) {
            scrambleCounts[i] = settings.scramble;
            scrambleArray[i] = getRandomChar(settings.range);
          }

          if (scrambleCounts[i] > 0) {
            result += getRandomChar(settings.range);
            if (i <= currentIndex) {
              scrambleCounts[i]--;
            }
            isComplete = false;
          } else if (scrambleArray[i] !== null) {
            result += originalText[i];
          } else {
            result += originalText[i];
            isComplete = false;
          }
        }

        element.textContent = result;

        // Move forward
        if (frameCount % 2 === 0 && currentIndex < originalText.length) {
          currentIndex++;
        }

        if (!isComplete) {
          animationId = requestAnimationFrame(animate);
        } else if (settings.overdrive && frameCount < originalText.length + 20) {
          // Continue for a bit with overdrive
          animationId = requestAnimationFrame(animate);
        } else {
          element.textContent = originalText;
        }
      } else {
        animationId = requestAnimationFrame(animate);
      }
    }

    // Start animation
    animationId = requestAnimationFrame(animate);

    // Return cleanup function
    return function cleanup() {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      element.textContent = originalText;
    };
  }

  // Expose to global scope
  window.scrambleText = scrambleText;

  // Auto-initialize on hover for elements with data-scramble attribute
  document.addEventListener('DOMContentLoaded', function() {
    const scrambleElements = document.querySelectorAll('[data-scramble]');
    
    scrambleElements.forEach(function(element) {
      let cleanup = null;
      
      element.addEventListener('mouseenter', function() {
        if (cleanup) cleanup();
        cleanup = scrambleText(element);
      });
    });
  });
})();
