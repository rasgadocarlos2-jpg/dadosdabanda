/* Melhorias partilhadas: meta, favicon, idioma, skip-link, hamburger, hover/focus, SEO, A11y. */
(() => {
  // Idioma
  document.documentElement.lang = "pt-AO";

  const head = document.head;
  const add = (tag, attrs = {}) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
    head.appendChild(el);
    return el;
  };
  const has = (sel) => !!head.querySelector(sel);

  // Descrições por página (SEO)
  const DESCRICOES = {
    "/": "Os dados oficiais de Angola, finalmente legíveis. Painel macroeconómico, orçamento desmontado e catálogo MINFIN, com a fonte identificada em cada série.",
    "/index.html": "Os dados oficiais de Angola, finalmente legíveis. Painel macroeconómico, orçamento desmontado e catálogo MINFIN.",
    "/painel.html": "Painel macroeconómico de Angola — inflação, câmbio USD/AOA, PIB, taxa BNA, desemprego, OGE. Dados oficiais do INE, BNA, FMI e Banco Mundial.",
    "/orcamento.html": "Desmontador do Orçamento Geral do Estado de Angola 2011-2026. Para onde vai o dinheiro público: educação, saúde, defesa, serviço da dívida, por ano.",
    "/pdfs.html": "Catálogo de 331 PDFs oficiais do MINFIN de Angola — OGE 2010-2026, relatórios trimestrais de execução (REOGE) e Conta Geral do Estado (CGE).",
    "/regional.html": "Inflação por província em Angola. Variação mensal e acumulada do IPCN nas 18 províncias. Fonte: INE Angola.",
    "/comparar.html": "Comparador de séries estatísticas — põe duas fontes lado a lado e vê onde divergem. Útil para investigar revisões e metodologias diferentes.",
    "/series.html": "Catálogo completo de todas as séries estatísticas disponíveis sobre Angola na API Dados da Banda.",
    "/api.html": "API pública e gratuita de dados sobre Angola. Gera uma chave, faz o pedido e recebe JSON ou CSV com a fonte de cada valor.",
    "/metodologia.html": "Como recolhemos, verificamos e publicamos os dados oficiais de Angola. Estado de cada fonte e processo de autorização.",
    "/legislacao.html": "Base de dados de legislação angolana em preparação. Fontes oficiais pendentes de autorização.",
    "/sobre.html": "Projecto independente de dados abertos sobre Angola. Como surgiu, quem está por trás e como contribuir.",
    "/faq.html": "Perguntas frequentes sobre o Dados da Banda — como usar a API, de onde vêm os dados, como reportar erros.",
    "/contacto.html": "Contactar o Dados da Banda — reportar erros, sugerir séries, pedir colaboração.",
    "/privacidade.html": "Política de privacidade do Dados da Banda. O que guardamos e o que não guardamos.",
    "/economico.html": "Modo económico — sem imagens, gráficos nem animações. Para ligações lentas ou planos de dados limitados.",
    "/404.html": "Página não encontrada.",
  };
  const pathname = location.pathname.endsWith("/") ? location.pathname : location.pathname;
  const desc = DESCRICOES[pathname] || DESCRICOES["/"];

  // Favicon
  if (!has('link[rel="icon"]')) add("link", { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" });

  // Theme color
  if (!has('meta[name="theme-color"]')) add("meta", { name: "theme-color", content: "#14274E" });

  // Preconnect para fontes (perf)
  if (!has('link[rel="preconnect"][href*="fonts.googleapis"]')) {
    add("link", { rel: "preconnect", href: "https://fonts.googleapis.com" });
    add("link", { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" });
  }

  // description
  if (!has('meta[name="description"]')) add("meta", { name: "description", content: desc });

  // OpenGraph + Twitter cards
  const url = location.origin + location.pathname;
  const title = (document.title || "Dados da Banda").trim();
  const og = {
    "og:title": title, "og:description": desc, "og:url": url, "og:type": "website",
    "og:image": location.origin + "/og-image.png", "og:locale": "pt_AO",
    "og:site_name": "Dados da Banda",
  };
  const tw = {
    "twitter:card": "summary_large_image", "twitter:title": title, "twitter:description": desc,
    "twitter:image": location.origin + "/og-image.png",
  };
  for (const [p, c] of Object.entries(og)) if (!has(`meta[property="${p}"]`)) add("meta", { property: p, content: c });
  for (const [n, c] of Object.entries(tw)) if (!has(`meta[name="${n}"]`)) add("meta", { name: n, content: c });

  // Canonical
  if (!has('link[rel="canonical"]')) add("link", { rel: "canonical", href: url });

  // JSON-LD: organização (todas as páginas) + Dataset (quando aplicável)
  if (!has('script[type="application/ld+json"]')) {
    const ld = {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "Dados da Banda",
      "url": location.origin,
      "logo": location.origin + "/favicon.svg",
      "description": "Dados abertos sobre Angola — legislação, estatística e finanças públicas.",
      "sameAs": []
    };
    const s = document.createElement("script");
    s.type = "application/ld+json";
    s.textContent = JSON.stringify(ld);
    head.appendChild(s);
  }

  // Estilo partilhado (hamburger, skip-link, hover/focus, dropdown mobile)
  const style = document.createElement("style");
  style.textContent = `
    .ddb-skip { position: absolute; top: -40px; left: 8px; z-index: 1000; background: #14274E; color: #fff; padding: 8px 12px; border-radius: 6px; text-decoration: none; font: 600 14px 'IBM Plex Sans', sans-serif; transition: top .15s; }
    .ddb-skip:focus { top: 8px; outline: 2px solid #B80F2D; outline-offset: 2px; }
    a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible { outline: 2px solid #B80F2D; outline-offset: 2px; border-radius: 4px; }
    .ddb-burger { display: none; cursor: pointer; background: #fff; border: 1px solid #14274E; border-radius: 8px; padding: 10px 12px; font: 600 15px 'IBM Plex Sans', sans-serif; min-height: 44px; align-items: center; gap: 8px; }
    .ddb-burger[aria-expanded="true"] { background: #14274E; color: #fff; }
    .ddb-burger svg { display: block; }
    @media (max-width: 720px) {
      header nav { display: none !important; width: 100%; order: 10; }
      header nav.ddb-open { display: flex !important; flex-direction: column !important; gap: 4px !important; padding: 12px 0 4px; border-top: 1px solid #E3E6EA; margin-top: 8px; }
      header nav.ddb-open a { padding: 10px 0; font-size: 17px !important; }
      .ddb-burger { display: inline-flex; margin-left: auto; }
      header .btn:not(.ddb-burger), header a.btn { display: none; }
      header nav.ddb-open ~ .btn, header nav.ddb-open ~ a.btn { display: inline-flex !important; margin-top: 8px; }
    }
    a.btn { display: inline-flex; align-items: center; justify-content: center; text-decoration: none; }
    .btn:not(:disabled):hover { background: #F3F5F7; }
    .btn[style*="B80F2D"]:hover { opacity: .92; }
    @media (prefers-reduced-motion: no-preference) {
      .btn, a { transition: background-color .15s, color .15s, opacity .15s; }
    }
    header nav a[aria-current="page"] { font-weight: 600; color: #B80F2D; }
    body::before { content: ""; display: block; height: 5px; background: #B80F2D; }
    .ddb-logo { display: inline-flex; align-items: center; gap: 10px; font: 600 20px 'IBM Plex Sans', sans-serif; letter-spacing: -.016em; color: #14274E; white-space: nowrap; }
    .ddb-logo::before { content: ""; width: 28px; height: 28px; background: url(/static/simbolo.svg) center/contain no-repeat; flex: none; }
    .ddb-burger { color: #14274E; }
    main p a, main li a, main .mut a, main .ans a, main div > a[style*="#B80F2D"], main div > a[style*="--accent"], main div > a[style*="#7A4B00"] { text-decoration: underline; text-underline-offset: 2px; }
    /* A11y: loading state */
    [aria-busy="true"] { cursor: progress; }
  `;
  head.appendChild(style);

  // Skip link + hamburger — depois do DOM carregar
  const init = () => {
    // Skip link
    if (!document.querySelector(".ddb-skip")) {
      const skip = document.createElement("a");
      skip.href = "#main"; skip.className = "ddb-skip"; skip.textContent = "Saltar para o conteúdo";
      document.body.insertBefore(skip, document.body.firstChild);
      const main = document.querySelector("main");
      if (main && !main.id) main.id = "main";
    }

    // Hamburger
    const header = document.querySelector("header");
    if (!header) return;
    const nav = header.querySelector("nav");
    nav?.querySelector(`a[href="${location.pathname}"]`)?.setAttribute("aria-current", "page");
    if (!nav || header.querySelector(".ddb-burger")) return;
    const btn = document.createElement("button");
    btn.className = "ddb-burger";
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-controls", "ddb-nav");
    btn.setAttribute("aria-label", "Abrir menu");
    btn.innerHTML = '<svg width="18" height="14" viewBox="0 0 18 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="1" y1="2" x2="17" y2="2"/><line x1="1" y1="7" x2="17" y2="7"/><line x1="1" y1="12" x2="17" y2="12"/></svg>Menu';
    nav.id = "ddb-nav";
    const container = header.firstElementChild || header;
    container.appendChild(btn);
    btn.addEventListener("click", () => {
      const open = nav.classList.toggle("ddb-open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.setAttribute("aria-label", open ? "Fechar menu" : "Abrir menu");
    });
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
