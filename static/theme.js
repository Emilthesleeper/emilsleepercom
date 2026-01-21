function initTheme(defaultToDark = false) {
    const themeToggle = document.getElementById('themeToggle');

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (themeToggle) {
            themeToggle.setAttribute('aria-pressed', String(theme === 'dark'));
        }
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            setTheme(current === 'dark' ? 'light' : 'dark');
        });
    }

    const stored = localStorage.getItem('theme');
    if (stored) {
        setTheme(stored);
    } else if (defaultToDark) {
        setTheme('dark');
    }
}

document.addEventListener('DOMContentLoaded', () => initTheme());

