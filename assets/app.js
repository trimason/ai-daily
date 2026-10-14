(() => {
  const input = document.getElementById('search-input');
  if (!input) return;
  const buttons = [...document.querySelectorAll('[data-filter]')];
  const items = [...document.querySelectorAll('.search-item')];
  const count = document.getElementById('result-count');
  const empty = document.getElementById('empty-results');
  let category = 'all';
  const update = () => {
    const words = input.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let matches = 0;
    for (const item of items) {
      const visible = (category === 'all' || item.dataset.category === category)
        && words.every(word => item.dataset.search.includes(word));
      item.hidden = !visible;
      if (visible) matches += 1;
    }
    count.textContent = String(matches);
    empty.hidden = matches !== 0;
  };
  input.addEventListener('input', update);
  for (const button of buttons) {
    button.addEventListener('click', () => {
      category = button.dataset.filter;
      for (const candidate of buttons) {
        const selected = candidate === button;
        candidate.classList.toggle('selected', selected);
        candidate.setAttribute('aria-pressed', String(selected));
      }
      update();
    });
  }
})();
