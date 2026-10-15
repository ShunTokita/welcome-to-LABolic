// Shared pieces of the process minigames.
//
// A process run clears on a single Excellent, so the guide (target bands on
// the gauges, a prompt on the button to press) stays on for the whole run
// rather than fading out over three samples as in the analysis games.
(function(){
  "use strict";

  // One prompt bubble, centred above whichever element it is pointing at.
  function tips(root) {
    const pc = root.querySelector('.pc');
    const tip = document.createElement('div');
    tip.className = 'pc-tip';
    pc.appendChild(tip);
    let cur = null, text = '';
    return {
      show(el, t) {
        if (el === cur && t === text) return;
        cur = el; text = t;
        const a = el.getBoundingClientRect(), b = pc.getBoundingClientRect();
        tip.textContent = t;
        tip.style.left = (a.left + a.width / 2 - b.left) + 'px';
        tip.style.top = (a.top - b.top) + 'px';
        tip.classList.add('on');
      },
      hide() { cur = null; text = ''; tip.classList.remove('on'); },
    };
  }

  window.MGProc = { tips };
})();
