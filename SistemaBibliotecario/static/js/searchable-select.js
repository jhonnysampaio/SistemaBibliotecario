(() => {
    "use strict";

    const LIMITE_RESULTADOS = 50;

    function normalizar(texto) {
        return texto
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLocaleLowerCase("pt-BR")
            .trim();
    }

    function iniciarSeletor(select, indice) {
        if (select.dataset.searchableReady === "true") {
            return;
        }
        select.dataset.searchableReady = "true";

        const opcoes = Array.from(select.options).filter(
            (opcao) => opcao.value !== ""
        );
        const selecionadaInicial = select.options[select.selectedIndex];
        const idLista = `${select.id || `searchable-${indice}`}-resultados`;
        const idPesquisa = `${select.id || `searchable-${indice}`}-pesquisa`;

        const componente = document.createElement("div");
        componente.className = "searchable-select";

        const controle = document.createElement("div");
        controle.className = "searchable-select__control";

        const icone = document.createElement("i");
        icone.className = "bi bi-search searchable-select__icon";
        icone.setAttribute("aria-hidden", "true");

        const pesquisa = document.createElement("input");
        pesquisa.type = "search";
        pesquisa.id = idPesquisa;
        pesquisa.className = "form-control searchable-select__search";
        pesquisa.placeholder =
            select.dataset.searchPlaceholder || "Pesquisar e selecionar";
        pesquisa.autocomplete = "off";
        pesquisa.disabled = select.disabled;
        pesquisa.setAttribute("role", "combobox");
        pesquisa.setAttribute("aria-autocomplete", "list");
        pesquisa.setAttribute("aria-haspopup", "listbox");
        pesquisa.setAttribute("aria-expanded", "false");
        pesquisa.setAttribute("aria-controls", idLista);
        if (select.required) {
            pesquisa.setAttribute("aria-required", "true");
        }

        if (selecionadaInicial && selecionadaInicial.value) {
            pesquisa.value = selecionadaInicial.text.trim();
        }

        const limpar = document.createElement("button");
        limpar.type = "button";
        limpar.className = "searchable-select__clear";
        limpar.title = "Limpar seleção";
        limpar.setAttribute("aria-label", "Limpar seleção");
        limpar.innerHTML = '<i class="bi bi-x-lg" aria-hidden="true"></i>';
        limpar.hidden = !select.value;

        const alternar = document.createElement("button");
        alternar.type = "button";
        alternar.className = "searchable-select__toggle";
        alternar.title = "Mostrar opções";
        alternar.setAttribute("aria-label", "Mostrar opções");
        alternar.setAttribute("aria-controls", idLista);
        alternar.setAttribute("aria-expanded", "false");
        alternar.innerHTML =
            '<i class="bi bi-chevron-down" aria-hidden="true"></i>';

        const lista = document.createElement("div");
        lista.id = idLista;
        lista.className = "searchable-select__menu";
        lista.setAttribute("role", "listbox");

        select.parentNode.insertBefore(componente, select);
        componente.appendChild(select);
        componente.appendChild(controle);
        controle.appendChild(icone);
        controle.appendChild(pesquisa);
        controle.appendChild(limpar);
        controle.appendChild(alternar);
        componente.appendChild(lista);
        select.classList.add("searchable-select__native");
        select.tabIndex = -1;

        const label = document.querySelector(`label[for="${select.id}"]`);
        if (label) {
            label.htmlFor = idPesquisa;
        }

        let resultados = [];
        let indiceAtivo = -1;

        function abrir() {
            componente.classList.add("is-open");
            pesquisa.setAttribute("aria-expanded", "true");
            alternar.setAttribute("aria-expanded", "true");
            alternar.setAttribute("aria-label", "Ocultar opções");
        }

        function fechar() {
            componente.classList.remove("is-open");
            pesquisa.setAttribute("aria-expanded", "false");
            alternar.setAttribute("aria-expanded", "false");
            alternar.setAttribute("aria-label", "Mostrar opções");
            pesquisa.removeAttribute("aria-activedescendant");
            indiceAtivo = -1;
        }

        function escolher(opcao) {
            select.value = opcao.value;
            pesquisa.value = opcao.text.trim();
            limpar.hidden = false;
            select.dispatchEvent(new Event("change", { bubbles: true }));
            renderizar(pesquisa.value);
            fechar();
            pesquisa.focus();
        }

        function ativar(novoIndice) {
            if (!resultados.length) {
                return;
            }
            indiceAtivo = (novoIndice + resultados.length) % resultados.length;
            resultados.forEach((resultado, atual) => {
                resultado.classList.toggle("is-active", atual === indiceAtivo);
            });
            const ativo = resultados[indiceAtivo];
            pesquisa.setAttribute("aria-activedescendant", ativo.id);
            ativo.scrollIntoView({ block: "nearest" });
        }

        function renderizar(termo = "") {
            const busca = normalizar(termo);
            const encontradas = opcoes.filter((opcao) =>
                normalizar(opcao.text).includes(busca)
            );
            const visiveis = encontradas.slice(0, LIMITE_RESULTADOS);

            lista.replaceChildren();
            resultados = [];
            indiceAtivo = -1;

            if (!visiveis.length) {
                const vazio = document.createElement("div");
                vazio.className = "searchable-select__empty";
                vazio.textContent =
                    select.dataset.searchEmpty || "Nenhum resultado encontrado.";
                lista.appendChild(vazio);
                return;
            }

            visiveis.forEach((opcao, posicao) => {
                const item = document.createElement("button");
                item.type = "button";
                item.id = `${idLista}-opcao-${posicao}`;
                item.className = "searchable-select__option";
                item.setAttribute("role", "option");
                item.setAttribute(
                    "aria-selected",
                    String(select.value === opcao.value)
                );

                const texto = document.createElement("span");
                texto.textContent = opcao.text.trim();
                item.appendChild(texto);

                if (select.value === opcao.value) {
                    const check = document.createElement("i");
                    check.className = "bi bi-check-lg searchable-select__check";
                    check.setAttribute("aria-hidden", "true");
                    item.appendChild(check);
                }

                item.addEventListener("mousedown", (evento) => {
                    evento.preventDefault();
                    escolher(opcao);
                });
                lista.appendChild(item);
                resultados.push(item);
            });

            if (encontradas.length > LIMITE_RESULTADOS) {
                const dica = document.createElement("div");
                dica.className = "searchable-select__hint";
                dica.textContent =
                    "Há mais resultados. Continue digitando para refinar.";
                lista.appendChild(dica);
            }
        }

        pesquisa.addEventListener("focus", () => {
            renderizar("");
            abrir();
        });

        pesquisa.addEventListener("input", () => {
            const selecionada = select.options[select.selectedIndex];
            if (
                !selecionada ||
                normalizar(pesquisa.value) !== normalizar(selecionada.text)
            ) {
                select.value = "";
                limpar.hidden = true;
            }
            renderizar(pesquisa.value);
            abrir();
        });

        pesquisa.addEventListener("keydown", (evento) => {
            if (evento.key === "ArrowDown") {
                evento.preventDefault();
                if (!componente.classList.contains("is-open")) {
                    renderizar("");
                    abrir();
                }
                ativar(indiceAtivo + 1);
            } else if (evento.key === "ArrowUp") {
                evento.preventDefault();
                ativar(indiceAtivo - 1);
            } else if (evento.key === "Enter" && indiceAtivo >= 0) {
                evento.preventDefault();
                resultados[indiceAtivo].dispatchEvent(
                    new MouseEvent("mousedown", { bubbles: true })
                );
            } else if (evento.key === "Escape") {
                fechar();
            }
        });

        limpar.addEventListener("click", () => {
            select.value = "";
            pesquisa.value = "";
            limpar.hidden = true;
            select.dispatchEvent(new Event("change", { bubbles: true }));
            renderizar();
            abrir();
            pesquisa.focus();
        });

        alternar.addEventListener("click", () => {
            if (componente.classList.contains("is-open")) {
                pesquisa.focus();
                fechar();
                return;
            }
            pesquisa.focus({ preventScroll: true });
            renderizar("");
            abrir();
        });

        select.addEventListener("change", () => {
            const selecionada = select.options[select.selectedIndex];
            pesquisa.value =
                selecionada && selecionada.value
                    ? selecionada.text.trim()
                    : "";
            limpar.hidden = !select.value;
        });

        if (select.form) {
            select.form.addEventListener("reset", () => {
                window.setTimeout(() => {
                    select.dispatchEvent(new Event("change"));
                    fechar();
                });
            });
        }

        document.addEventListener("mousedown", (evento) => {
            if (!componente.contains(evento.target)) {
                fechar();
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        document
            .querySelectorAll("select[data-searchable-select]")
            .forEach(iniciarSeletor);
    });
})();
