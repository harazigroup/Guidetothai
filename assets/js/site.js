(function () {
  // Dropdown menus: click/tap opens the list, a second click closes it.
  function closeAll(keep) {
    document.querySelectorAll('.gt-dd.open').forEach(function (d) {
      if (d !== keep) {
        d.classList.remove('open');
        var t = d.querySelector('.gt-dd-t');
        if (t) t.setAttribute('aria-expanded', 'false');
      }
    });
  }
  document.querySelectorAll('.gt-dd-t').forEach(function (t) {
    t.setAttribute('role', 'button');
    t.setAttribute('aria-haspopup', 'true');
    t.setAttribute('aria-expanded', 'false');
    t.addEventListener('click', function (e) {
      e.preventDefault();
      var d = t.parentNode;
      closeAll(d);
      d.classList.toggle('open');
      t.setAttribute('aria-expanded', d.classList.contains('open'));
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.gt-dd')) closeAll(null);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeAll(null);
  });

  // Highlight the current section in the menu.
  var here = location.pathname.replace(/index\.html$/, '');
  document.querySelectorAll('.gt-nav2 > a.gt-mi').forEach(function (a) {
    var p = a.getAttribute('href');
    if (p && p.length > 4 && here.indexOf(p) === 0) a.classList.add('on');
  });

  // Gallery filter (Our Work page).
  var filters = document.querySelectorAll('.gt-filter');
  filters.forEach(function (b) {
    b.addEventListener('click', function () {
      filters.forEach(function (x) { x.classList.remove('on'); x.setAttribute('aria-pressed', 'false'); });
      b.classList.add('on');
      b.setAttribute('aria-pressed', 'true');
      var k = b.getAttribute('data-f');
      document.querySelectorAll('.gt-tile').forEach(function (t) {
        t.classList.toggle('hide', k !== 'all' && t.getAttribute('data-cat') !== k);
      });
    });
  });

  // Blog category filter.
  var bf = document.querySelectorAll('.gt-bfilter');
  bf.forEach(function (b) {
    b.addEventListener('click', function () {
      bf.forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      var k = b.getAttribute('data-f');
      document.querySelectorAll('.gt-post-card').forEach(function (c) {
        c.style.display = (k === 'all' || c.getAttribute('data-cat') === k) ? '' : 'none';
      });
    });
  });
})();
