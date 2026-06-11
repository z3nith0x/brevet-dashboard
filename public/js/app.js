const API_BASE = '/api';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  const loginSection = document.getElementById('login-section');
  const resultsSection = document.getElementById('results-section');
  const errorMsg = document.getElementById('error-message');
  const submitBtn = document.getElementById('submit-btn');
  const btnText = document.getElementById('btn-text');
  const btnSpinner = document.getElementById('btn-spinner');
  const backBtn = document.getElementById('back-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMsg.classList.add('hidden');

    const payload = {
      url: document.getElementById('url').value.trim(),
      username: document.getElementById('username').value.trim(),
      password: document.getElementById('password').value,
      ent: document.getElementById('ent').value,
    };

    if (!payload.url || !payload.username || !payload.password) {
      showError('Tous les champs obligatoires doivent être remplis.');
      return;
    }

    submitBtn.disabled = true;
    btnText.textContent = 'Connexion à Pronote…';
    btnSpinner.classList.remove('hidden');

    try {
      const res = await fetch(`${API_BASE}/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (data.error) {
        showError(data.error);
        return;
      }

      displayResults(data);
      loginSection.classList.add('hidden');
      resultsSection.classList.remove('hidden');

    } catch (err) {
      showError('Erreur de connexion au serveur. Vérifie que le backend est lancé.');
    } finally {
      submitBtn.disabled = false;
      btnText.textContent = 'Calculer mon contrôle continu';
      btnSpinner.classList.add('hidden');
    }
  });

  backBtn.addEventListener('click', () => {
    resultsSection.classList.add('hidden');
    loginSection.classList.remove('hidden');
    errorMsg.classList.add('hidden');
  });

  function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.classList.remove('hidden');
  }

  function displayResults(data) {
    document.getElementById('student-info').textContent =
      `${data.student} — ${data.class} — ${data.school}`;

    document.getElementById('final-score').textContent = data.final_controle_continu.toFixed(2);
    document.getElementById('brevet-impact').textContent = data.brevet_40_percent.toFixed(2);
    document.getElementById('sum-mandatory').textContent = data.mandatory_sum.toFixed(2);
    document.getElementById('count-mandatory').textContent = data.mandatory_count;
    document.getElementById('total-sum').textContent = data.total_sum.toFixed(2);
    document.getElementById('divisor-count').textContent = data.mandatory_count;
    document.getElementById('calculated-average').textContent =
      `${data.total_sum.toFixed(2)} ÷ ${data.mandatory_count} = ${data.final_controle_continu.toFixed(2)}`;

    const capRow = document.getElementById('cap-row');
    if (data.capped) {
      capRow.style.display = 'flex';
    } else {
      capRow.style.display = 'none';
    }

    // Bonus
    const bonusRow = document.getElementById('bonus-row');
    const bonusValue = document.getElementById('bonus-value');
    if (data.optional_bonus_total > 0) {
      bonusRow.style.display = 'flex';
      bonusValue.textContent = `+${data.optional_bonus_total.toFixed(2)}`;
      bonusValue.className = 'detail-value bonus-value';
    } else {
      bonusRow.style.display = 'none';
    }

    // Optional subjects detail
    const optSection = document.getElementById('optional-section');
    const optList = document.getElementById('optional-list');
    if (data.optional_subjects && data.optional_subjects.length > 0) {
      optSection.style.display = 'block';
      optList.innerHTML = data.optional_subjects.map(o => `
        <div class="optional-item">
          <span class="subj-name">${escapeHtml(o.subject)}</span>
          <span class="subj-detail">Moyenne : ${o.average.toFixed(2)}/20</span>
          <span class="bonus-pts">+${o.bonus.toFixed(2)} pts</span>
        </div>
      `).join('');
    } else {
      optSection.style.display = 'none';
    }

    // Subjects table
    const tbody = document.getElementById('subjects-body');
    const allSubjects = [
      ...(data.subjects || []).map(s => ({ ...s, type: 'Obligatoire', tag: 'tag-mandatory' })),
      ...(data.optional_subjects || []).map(s => ({ ...s, type: 'Option', tag: 'tag-optional' })),
    ];
    tbody.innerHTML = allSubjects.map(s => `
      <tr>
        <td>${escapeHtml(s.subject)}</td>
        <td><strong>${s.average.toFixed(2)}</strong> / 20</td>
        <td><span class="${s.tag}">${s.type}</span></td>
      </tr>
    `).join('');
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
});
