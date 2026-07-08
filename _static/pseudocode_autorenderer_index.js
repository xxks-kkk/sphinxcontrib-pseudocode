window.MathJax = window.MathJax || {};
window.MathJax.tex = window.MathJax.tex || {};
window.MathJax.tex.macros = Object.assign({"ceil": ["\\lceil #1 \\rceil", 1], "floor": ["\\lfloor #1 \\rfloor", 1]}, window.MathJax.tex.macros || {});
document.addEventListener("DOMContentLoaded", function() {
  var renderAll = function() {
    
    (function() {
        var pcsEl = document.getElementById("1");
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 0,
             lineNumber: true 
        });
        
    })();
    (function() {
        var pcsEl = document.getElementById("2");
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 1,
            
        });
        
    })();
    (function() {
        var pcsEl = document.getElementById("3");
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 2,
            
        });
        
    })();
    (function() {
        var pcsEl = document.getElementById("4");
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 3,
            
        });
        
    })();
    (function() {
        var pcsEl = document.getElementById("5");
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 4,
            
        });
        
    })();
    (function() {
        var pcsEl = document.getElementById("6");
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 5,
            
        });
        
    })();
    (function() {
        var pcsEl = document.getElementById("7");
        
        var pcsContainer = pcsEl ? pcsEl.parentElement : null;
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 6,
            
        });
        
        if (pcsContainer) {
            var refs = [{"placeholder": "PCSREF0", "text": "Quicksort", "href": "#quick-sort"}];
            var html = pcsContainer.innerHTML;
            refs.forEach(function(r) {
                html = html.split(r.placeholder).join('<a href="' + r.href + '">' + r.text + '</a>');
            });
            pcsContainer.innerHTML = html;
        }
        
    })();
    (function() {
        var pcsEl = document.getElementById("8");
        
        var pcsContainer = pcsEl ? pcsEl.parentElement : null;
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 7,
            
        });
        
        if (pcsContainer) {
            var refs = [{"placeholder": "PCSREF0", "text": "(1)", "href": "#equation-euclidean-norm"}];
            var html = pcsContainer.innerHTML;
            refs.forEach(function(r) {
                html = html.split(r.placeholder).join('<a href="' + r.href + '">' + r.text + '</a>');
            });
            pcsContainer.innerHTML = html;
        }
        
    })();
    (function() {
        var pcsEl = document.getElementById("9");
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 8,
            
        });
        
    })();
    (function() {
        var pcsEl = document.getElementById("10");
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 9,
            
        });
        
    })();
    (function() {
        var pcsEl = document.getElementById("11");
        
        pseudocode.renderElement(pcsEl, {
            captionCount: 10,
            
        });
        
    })();
    if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
      MathJax.typesetPromise();
    }
  };
  if (typeof MathJax !== 'undefined' && MathJax.startup) {
    MathJax.startup.promise.then(renderAll);
  } else {
    renderAll();
  }
});