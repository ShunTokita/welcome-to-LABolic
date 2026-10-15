// Shared pieces of the process minigames.
//
// A process run clears on a single Excellent, so the guide (target bands on
// the gauges, a prompt on the button to press) stays on for the whole run
// rather than fading out over three samples as in the analysis games.
(function(){
  "use strict";

  // One prompt bubble above whichever element it is pointing at: centred
  // on it where there is room, slid inward at the edges with its arrow
  // still on the element.
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
        tip.classList.add('on');
        const cx = a.left + a.width / 2 - b.left, half = tip.offsetWidth / 2;
        const x = Math.max(half + 2, Math.min(b.width - half - 2, cx));
        tip.style.left = x + 'px';
        tip.style.top = (a.top - b.top) + 'px';
        tip.style.setProperty('--ax', (cx - x) + 'px');
      },
      hide() { cur = null; text = ''; tip.classList.remove('on'); },
    };
  }

  window.MGProc = { tips };
})();
