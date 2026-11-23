(() => {
    "use strict";

    // Evita enviar o mesmo formulário duas vezes (duplo clique no botão).
    document.querySelectorAll("form[data-importacao-form]").forEach((form) => {
        form.addEventListener("submit", () => {
            const botao = form.querySelector("button[type='submit']");
            if (!botao) {
                return;
            }

            // Deixa o navegador iniciar o envio antes de desativar o botão.
            setTimeout(() => {
                botao.disabled = true;
                botao.textContent = botao.dataset.textoEnviando || "Processando...";
            }, 0);
        });
    });
})();
