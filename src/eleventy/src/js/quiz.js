/**
 * Quiz component -- interactive multiple-choice.
 * Transforms checkbox lists inside .component--quiz into clickable options.
 */

export function initQuiz() {
  const quizzes = document.querySelectorAll('.component--quiz');
  if (!quizzes.length) return;

  quizzes.forEach(quiz => {
    const body = quiz.querySelector('.component__body');
    if (!body) return;

    // Find the list with checkboxes
    const list = body.querySelector('ul, ol');
    if (!list) return;

    const items = list.querySelectorAll('li');
    if (!items.length) return;

    // Parse correct answers from checked inputs
    const options = [];
    items.forEach(li => {
      const checkbox = li.querySelector('input[type="checkbox"]');
      const isCorrect = checkbox ? checkbox.checked : false;
      const text = li.textContent.trim();
      options.push({ text, isCorrect });
    });

    // Replace list with interactive options
    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'quiz__options';

    options.forEach((opt, i) => {
      const optEl = document.createElement('div');
      optEl.className = 'quiz__option';
      optEl.textContent = opt.text;
      optEl.dataset.correct = opt.isCorrect;
      optEl.dataset.index = i;
      optionsContainer.appendChild(optEl);
    });

    // Reset button
    const resetBtn = document.createElement('button');
    resetBtn.className = 'quiz__reset';
    resetBtn.textContent = 'Reintentar';
    resetBtn.type = 'button';

    // Replace original list
    list.replaceWith(optionsContainer);
    optionsContainer.after(resetBtn);

    // Click handler
    let answered = false;
    optionsContainer.addEventListener('click', (e) => {
      const option = e.target.closest('.quiz__option');
      if (!option || answered) return;

      answered = true;

      // Reveal all answers
      optionsContainer.querySelectorAll('.quiz__option').forEach(opt => {
        opt.classList.add('quiz__option--disabled');
        if (opt.dataset.correct === 'true') {
          opt.classList.add('quiz__option--correct');
        }
      });

      // Mark selected if incorrect
      if (option.dataset.correct !== 'true') {
        option.classList.add('quiz__option--incorrect');
      }

      resetBtn.style.display = 'inline-block';
    });

    // Reset handler
    resetBtn.addEventListener('click', () => {
      answered = false;
      resetBtn.style.display = 'none';
      optionsContainer.querySelectorAll('.quiz__option').forEach(opt => {
        opt.classList.remove('quiz__option--correct', 'quiz__option--incorrect', 'quiz__option--disabled');
      });
    });
  });
}
