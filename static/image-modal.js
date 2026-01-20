(function(){
    // Simple image modal for images inside .gallery
    function openImage(src, alt){
        const overlay = document.createElement('div');
        overlay.className = 'img-modal-overlay';
        overlay.tabIndex = 0;

        const container = document.createElement('div');
        container.className = 'img-modal-content';

        const img = document.createElement('img');
        img.src = src;
        img.alt = alt || '';
        container.appendChild(img);
        overlay.appendChild(container);

        // Close handler
        function close(){
            if(overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
            document.removeEventListener('keydown', onKey);
        }
        function onKey(e){ if(e.key === 'Escape') close(); }

        overlay.addEventListener('click', close);
        document.addEventListener('keydown', onKey);

        document.body.appendChild(overlay);
        overlay.focus();
    }

    document.addEventListener('click', function(e){
        const img = e.target.closest('.gallery img');
        if(!img) return;
        e.preventDefault();
        openImage(img.dataset.full || img.src, img.alt);
    });
})();
