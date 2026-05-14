window.MathJax = window.MathJax || {};
window.MathJax.tex = window.MathJax.tex || {};
window.MathJax.tex.macros = Object.assign({"ceil": ["\\lceil #1 \\rceil", 1], "floor": ["\\lfloor #1 \\rfloor", 1]}, window.MathJax.tex.macros || {});
document.addEventListener("DOMContentLoaded", function() {
  var renderAll = function() {
     
    pseudocode.renderElement(
    document.getElementById("1"), {
        captionCount: 0,
         lineNumber: true 
    });
 
    pseudocode.renderElement(
    document.getElementById("2"), {
        captionCount: 1,
        
    });
 
    pseudocode.renderElement(
    document.getElementById("3"), {
        captionCount: 2,
        
    });
 
    pseudocode.renderElement(
    document.getElementById("4"), {
        captionCount: 3,
        
    });
 
    pseudocode.renderElement(
    document.getElementById("5"), {
        captionCount: 4,
        
    });
 
    pseudocode.renderElement(
    document.getElementById("6"), {
        captionCount: 5,
        
    });
 
    pseudocode.renderElement(
    document.getElementById("7"), {
        captionCount: 6,
        
    });
 
    pseudocode.renderElement(
    document.getElementById("8"), {
        captionCount: 7,
        
    });
 
    pseudocode.renderElement(
    document.getElementById("9"), {
        captionCount: 8,
        
    });

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