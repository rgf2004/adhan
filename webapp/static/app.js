document.addEventListener('DOMContentLoaded', function () {
  setupAudioTestPlay();
  setupSettingsModeToggle();
  setupMawaqitCredentials();
});

function setupAudioTestPlay() {
  document.querySelectorAll('.test-play-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var row = btn.closest('tr');
      var volume = row.querySelector('.test-volume').value || 100;
      fetch('/audio/test-play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: btn.dataset.path, volume: volume }),
      }).then(function (res) {
        document.getElementById('play-status').textContent = res.ok ? 'Playing…' : 'Error starting playback';
      });
    });
  });

  var stopBtn = document.getElementById('stop-play-btn');
  if (stopBtn) {
    stopBtn.addEventListener('click', function () {
      fetch('/audio/stop', { method: 'POST' }).then(function () {
        document.getElementById('play-status').textContent = '';
      });
    });
  }
}

// Settings page: only show the fieldset relevant to the selected mode.
function setupSettingsModeToggle() {
  var modeSelect = document.getElementById('mode-select');
  var fieldsets = document.querySelectorAll('.mode-fieldset');
  if (!modeSelect || !fieldsets.length) return;

  function update() {
    fieldsets.forEach(function (fs) {
      fs.classList.toggle('hidden-mode', fs.dataset.mode !== modeSelect.value);
    });
  }
  modeSelect.addEventListener('change', update);
  update();
}

// Mawaqit page: one shared username/password card feeds every action form,
// instead of repeating the fields on each form.
function setupMawaqitCredentials() {
  var userInput = document.getElementById('mw-username');
  var passInput = document.getElementById('mw-password');
  if (!userInput || !passInput) return;

  document.querySelectorAll('form.mawaqit-form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!userInput.value || !passInput.value) {
        e.preventDefault();
        userInput.focus();
        return;
      }
      var u = form.querySelector('input[name=username]');
      var p = form.querySelector('input[name=password]');
      if (u) u.value = userInput.value;
      if (p) p.value = passInput.value;
    });
  });
}
