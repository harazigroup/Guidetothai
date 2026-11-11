/* guidetothai — airport arrival booking & Stripe Embedded Checkout.
   Config comes from <div id="gt-co" data-fn data-pk data-lang data-wa> and strings from <script id="gt-co-i18n">. */
(function () {
  var root = document.getElementById('gt-co');
  if (!root) return;
  var FN = root.getAttribute('data-fn'), PK = root.getAttribute('data-pk'), LANG = root.getAttribute('data-lang') || 'en';
  var WA = root.getAttribute('data-wa');
  var T = JSON.parse(document.getElementById('gt-co-i18n').textContent);
  var PRICES = { vip: 6000, standard: 1500 };
  var form = document.getElementById('gt-co-form'), payBox = document.getElementById('gt-co-pay'),
      done = document.getElementById('gt-co-done'), err = document.getElementById('gt-co-err'),
      btn = document.getElementById('gt-co-submit');
  var fmt = function (n) { return '฿' + Number(n).toLocaleString('en-US'); };
  var $ = function (n) { return form.elements[n]; };

  // ----- package from URL (?pkg=standard) -----
  var qs = new URLSearchParams(location.search);
  if (qs.get('pkg') === 'standard') $('pkg').value = 'standard';

  // ----- min date: tomorrow (Bangkok) -----
  var t = new Date(Date.now() + 7 * 3600e3 + 24 * 3600e3);
  $('date').min = t.toISOString().slice(0, 10);

  function summary() {
    var pkg = $('pkg').value, pax = Math.max(1, Math.min(10, parseInt($('pax').value || '1', 10)));
    document.getElementById('gt-co-s-pkg').textContent = T.pkgs[pkg];
    document.getElementById('gt-co-s-unit').textContent = fmt(PRICES[pkg]) + ' × ' + pax;
    document.getElementById('gt-co-s-total').textContent = fmt(PRICES[pkg] * pax);
    document.querySelectorAll('.gt-co-pkg').forEach(function (el) { el.classList.toggle('on', el.querySelector('input').checked); });
  }
  form.addEventListener('input', summary);
  form.addEventListener('change', summary);
  summary();

  function data() {
    var o = { lang: LANG };
    ['pkg', 'name', 'email', 'phone', 'date', 'time', 'flight', 'airport', 'pax', 'hotel', 'bags', 'notes'].forEach(function (k) { o[k] = ($(k).value || '').trim(); });
    return o;
  }
  function waText(d, ref) {
    return [T.wa_intro, ref ? T.ref + ': ' + ref : '', T.pkgs[d.pkg], T.f.name + ': ' + d.name, T.f.flight + ': ' + d.flight,
      T.f.date + ': ' + d.date + ' ' + d.time, T.f.airport + ': ' + d.airport, T.f.pax + ': ' + d.pax, T.f.hotel + ': ' + d.hotel,
      T.f.phone + ': ' + d.phone].filter(Boolean).join('\n');
  }
  function showErr(m) { err.textContent = m; err.hidden = !m; if (m) err.scrollIntoView({ behavior: 'smooth', block: 'center' }); }

  function loadStripe(cb) {
    if (window.Stripe) return cb();
    var s = document.createElement('script'); s.src = 'https://js.stripe.com/v3/'; s.onload = cb;
    s.onerror = function () { showErr(T.err_net); btn.disabled = false; }; document.head.appendChild(s);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault(); showErr('');
    if (!form.checkValidity()) { form.reportValidity(); return; }
    var d = data();
    if (!PK || !FN) { // payments not switched on yet → book on WhatsApp
      window.open('https://wa.me/' + WA + '?text=' + encodeURIComponent(waText(d)), '_blank'); return;
    }
    btn.disabled = true; btn.textContent = T.loading;
    fetch(FN, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.assign({ action: 'start' }, d)) })
      .then(function (r) { return r.json().then(function (b) { return { ok: r.ok, b: b }; }); })
      .then(function (res) {
        if (!res.ok || !res.b.clientSecret) {
          var f = (res.b && res.b.fields) || [];
          throw new Error(f.length ? T.err_fields + ' ' + f.map(function (k) { return T.f[k] || k; }).join('، ') : T.err_generic);
        }
        try { sessionStorage.setItem('gt-co-last', JSON.stringify(Object.assign({ ref: res.b.ref }, d))); } catch (x) {}
        loadStripe(function () {
          Stripe(PK).initEmbeddedCheckout({ fetchClientSecret: function () { return Promise.resolve(res.b.clientSecret); } })
            .then(function (co) { form.hidden = true; payBox.hidden = false; co.mount('#gt-co-stripe'); payBox.scrollIntoView({ behavior: 'smooth' }); });
        });
      })
      .catch(function (x) { showErr(x.message || T.err_generic); btn.disabled = false; btn.textContent = T.pay; });
  });

  // ----- back from Stripe -----
  var sid = qs.get('session_id');
  if (sid && FN) {
    form.hidden = true; done.hidden = false;
    fetch(FN, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'status', session_id: sid }) })
      .then(function (r) { return r.json(); })
      .then(function (s) {
        var paid = s.status === 'paid';
        document.getElementById('gt-co-done-h').textContent = paid ? T.done_ok : T.done_wait;
        document.getElementById('gt-co-done-ref').textContent = s.ref || '';
        document.getElementById('gt-co-done-d').textContent = [s.flight, s.date + ' ' + (s.time || ''), s.airport, T.f.pax + ' ' + s.pax, fmt(s.total)].join(' · ');
        var last = {}; try { last = JSON.parse(sessionStorage.getItem('gt-co-last') || '{}'); } catch (x) {}
        var d = Object.assign({ pkg: s.pkg || 'vip', name: s.name, flight: s.flight, date: s.date, time: s.time, airport: s.airport, pax: s.pax, hotel: '', phone: '' }, last);
        document.getElementById('gt-co-done-wa').href = 'https://wa.me/' + WA + '?text=' + encodeURIComponent((paid ? T.wa_paid + '\n' : '') + waText(d, s.ref));
      })
      .catch(function () { document.getElementById('gt-co-done-h').textContent = T.done_wait; });
  }
})();
