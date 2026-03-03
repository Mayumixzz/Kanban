from pathlib import Path

HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Kanban</title>
  <style>
    :root { --bg:#0b1020; --card:#121a33; --muted:#8ea0c6; --line:#22305b; --text:#e8eeff; }
    *{ box-sizing:border-box; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; }
    body{ margin:0; background:var(--bg); color:var(--text); }
    header{
      position:sticky; top:0; z-index:5;
      display:flex; gap:12px; align-items:center; justify-content:space-between;
      padding:14px 16px; border-bottom:1px solid var(--line); background:rgba(11,16,32,.92); backdrop-filter: blur(10px);
    }
    header h1{ font-size:16px; margin:0; letter-spacing:.2px; }
    header .actions{ display:flex; gap:8px; flex-wrap:wrap; }
    button{
      border:1px solid var(--line); background:var(--card); color:var(--text);
      padding:8px 10px; border-radius:10px; cursor:pointer; font-size:13px;
    }
    button:hover{ filter:brightness(1.08); }
    main{ padding:14px 16px; }
    .board{
      display:grid; gap:12px;
      grid-template-columns: repeat(4, minmax(260px, 1fr));
      align-items:start;
    }
    @media (max-width: 1100px){ .board{ grid-template-columns: repeat(2, minmax(260px, 1fr)); } }
    @media (max-width: 640px){ .board{ grid-template-columns: 1fr; } }

    .col{
      background:rgba(18,26,51,.7); border:1px solid var(--line);
      border-radius:16px; padding:10px; min-height:260px;
    }
    .col header{
      position:static; background:transparent; border:none; padding:6px 6px 10px 6px;
      display:flex; justify-content:space-between; align-items:center;
    }
    .col header h2{ font-size:13px; margin:0; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }
    .col header .count{ font-size:12px; color:var(--muted); }
    .dropzone{ display:flex; flex-direction:column; gap:10px; padding:6px; border-radius:12px; }
    .dropzone.dragover{ outline:2px dashed #3f59ff; outline-offset: 2px; }

    .card{
      background:var(--card); border:1px solid var(--line);
      border-radius:14px; padding:10px; cursor:grab;
    }
    .card:active{ cursor:grabbing; }
    .title{ font-weight:600; font-size:14px; margin:0 0 6px 0; }
    .meta{ font-size:12px; color:var(--muted); display:flex; gap:8px; flex-wrap:wrap; }
    .tag{
      border:1px solid var(--line); padding:2px 8px; border-radius:999px;
    }
    .toolbar{ margin-top:8px; display:flex; gap:8px; }
    .toolbar button{ padding:6px 8px; font-size:12px; border-radius:10px; }
    .small{ font-size:12px; color:var(--muted); }
    .modal{
      position:fixed; inset:0; display:none; place-items:center; background:rgba(0,0,0,.55); z-index:20;
      padding:16px;
    }
    .modal.show{ display:grid; }
    .panel{
      width:min(720px, 100%); background:var(--card); border:1px solid var(--line);
      border-radius:16px; padding:14px;
    }
    .panel h3{ margin:0 0 10px 0; font-size:14px; color:var(--muted); }
    .row{ display:grid; gap:10px; grid-template-columns: 1fr 1fr; }
    @media (max-width: 640px){ .row{ grid-template-columns:1fr; } }
    input, textarea, select{
      width:100%; padding:10px; border-radius:12px; border:1px solid var(--line);
      background:#0e1631; color:var(--text); font-size:13px;
    }
    textarea{ min-height:110px; resize:vertical; }
    .panel .actions{ display:flex; justify-content:flex-end; gap:8px; margin-top:10px; }
    .danger{ border-color:#6b2c2c; }
  </style>
</head>
<body>
<header>
  <h1>Kanban</h1>
  <div class="actions">
    <button id="btnAdd">+ Novo cartão</button>
    <button id="btnAddCol">+ Nova coluna</button>
    <button id="btnExport">Exportar JSON</button>
    <button id="btnImport">Importar JSON</button>
    <button id="btnReset" class="danger">Reset</button>
  </div>
</header>

<main>
  <div class="small">Dica: arraste cartões entre colunas. Tudo salva automaticamente no seu navegador.</div>
  <div id="board" class="board" aria-label="Quadro Kanban"></div>
</main>

<div id="modal" class="modal" role="dialog" aria-modal="true">
  <div class="panel">
    <h3 id="modalTitle">Novo cartão</h3>
    <div class="row">
      <div>
        <label class="small">Título</label>
        <input id="fTitle" placeholder="Ex: Levantar dados de iluminação" />
      </div>
      <div>
        <label class="small">Coluna</label>
        <select id="fCol"></select>
      </div>
      <div>
        <label class="small">Tag</label>
        <input id="fTag" placeholder="Ex: FIAP / Pesquisa / Urgente" />
      </div>
      <div>
        <label class="small">Prazo</label>
        <input id="fDue" type="date" />
      </div>
    </div>
    <div style="margin-top:10px;">
      <label class="small">Descrição</label>
      <textarea id="fDesc" placeholder="Notas do cartão..."></textarea>
    </div>
    <div class="actions">
      <button id="btnCancel">Cancelar</button>
      <button id="btnSave">Salvar</button>
    </div>
  </div>
</div>

<div id="modalImport" class="modal" role="dialog" aria-modal="true">
  <div class="panel">
    <h3>Importar JSON</h3>
    <div class="small">Cole aqui um JSON exportado do seu Kanban.</div>
    <textarea id="importArea" placeholder='{"columns":[...],"cards":[...]}'></textarea>
    <div class="actions">
      <button id="btnCancelImport">Cancelar</button>
      <button id="btnDoImport">Importar</button>
    </div>
  </div>
</div>

<script>
  const STORAGE_KEY = "kanban_v1";

  const uid = () => Math.random().toString(16).slice(2) + Date.now().toString(16);

  const defaultState = () => ({
    columns: [
      { id: "todo", title: "A Fazer" },
      { id: "doing", title: "Em Progresso" },
      { id: "review", title: "Revisão" },
      { id: "done", title: "Concluído" },
    ],
    cards: [
      { id: uid(), col: "todo", title: "Definir perguntas da pesquisa", desc: "", tag: "FIAP", due: "" },
      { id: uid(), col: "todo", title: "Mapear pontos críticos no trajeto", desc: "", tag: "Exploratória", due: "" },
    ]
  });

  const load = () => {
    try{
      const raw = localStorage.getItem(STORAGE_KEY);
      if(!raw) return defaultState();
      const s = JSON.parse(raw);
      if(!s.columns || !s.cards) return defaultState();
      return s;
    }catch(e){
      return defaultState();
    }
  };

  const save = () => localStorage.setItem(STORAGE_KEY, JSON.stringify(state));

  let state = load();
  let draggingCardId = null;

  const board = document.getElementById("board");

  function render(){
    board.innerHTML = "";
    state.columns.forEach(col => {
      const cards = state.cards.filter(c => c.col === col.id);

      const colEl = document.createElement("section");
      colEl.className = "col";
      colEl.dataset.col = col.id;

      const header = document.createElement("header");
      const h2 = document.createElement("h2");
      h2.textContent = col.title;
      const count = document.createElement("div");
      count.className = "count";
      count.textContent = cards.length;

      const tools = document.createElement("div");
      tools.className = "toolbar";
      const addBtn = document.createElement("button");
      addBtn.textContent = "+";
      addBtn.title = "Adicionar cartão nesta coluna";
      addBtn.onclick = () => openModal({ col: col.id });

      const renameBtn = document.createElement("button");
      renameBtn.textContent = "Renomear";
      renameBtn.onclick = () => {
        const t = prompt("Novo nome da coluna:", col.title);
        if(t && t.trim()){
          col.title = t.trim();
          save(); render();
        }
      };

      const delBtn = document.createElement("button");
      delBtn.textContent = "Excluir";
      delBtn.className = "danger";
      delBtn.onclick = () => {
        if(confirm("Excluir coluna e mover cartões para 'A Fazer'?")){
          const todo = state.columns[0]?.id || "todo";
          state.cards.forEach(c => { if(c.col === col.id) c.col = todo; });
          state.columns = state.columns.filter(x => x.id !== col.id);
          save(); render();
        }
      };

      tools.append(addBtn, renameBtn, delBtn);
      header.append(h2, count);
      colEl.append(header);

      const dz = document.createElement("div");
      dz.className = "dropzone";
      dz.ondragover = (e) => { e.preventDefault(); dz.classList.add("dragover"); };
      dz.ondragleave = () => dz.classList.remove("dragover");
      dz.ondrop = (e) => {
        e.preventDefault();
        dz.classList.remove("dragover");
        if(!draggingCardId) return;
        const card = state.cards.find(c => c.id === draggingCardId);
        if(card){
          card.col = col.id;
          save(); render();
        }
      };

      cards.forEach(c => dz.appendChild(cardEl(c)));
      colEl.append(dz);

      board.append(colEl);
    });

    refreshColumnSelect();
  }

  function cardEl(c){
    const el = document.createElement("article");
    el.className = "card";
    el.draggable = true;
    el.ondragstart = () => { draggingCardId = c.id; };
    el.ondragend = () => { draggingCardId = null; };

    const t = document.createElement("div");
    t.className = "title";
    t.textContent = c.title;

    const meta = document.createElement("div");
    meta.className = "meta";

    if(c.tag){
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = c.tag;
      meta.append(tag);
    }
    if(c.due){
      const due = document.createElement("span");
      due.className = "tag";
      due.textContent = "📅 " + c.due;
      meta.append(due);
    }

    const actions = document.createElement("div");
    actions.className = "toolbar";

    const edit = document.createElement("button");
    edit.textContent = "Editar";
    edit.onclick = () => openModal(c);

    const del = document.createElement("button");
    del.textContent = "Excluir";
    del.className = "danger";
    del.onclick = () => {
      if(confirm("Excluir cartão?")){
        state.cards = state.cards.filter(x => x.id !== c.id);
        save(); render();
      }
    };

    actions.append(edit, del);

    el.append(t, meta, actions);
    return el;
  }

  const modal = document.getElementById("modal");
  const modalTitle = document.getElementById("modalTitle");
  const fTitle = document.getElementById("fTitle");
  const fDesc = document.getElementById("fDesc");
  const fTag  = document.getElementById("fTag");
  const fDue  = document.getElementById("fDue");
  const fCol  = document.getElementById("fCol");
  let editingId = null;

  function refreshColumnSelect(){
    fCol.innerHTML = "";
    state.columns.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.title;
      fCol.appendChild(opt);
    });
  }

  function openModal(cardOrDefaults){
    editingId = cardOrDefaults?.id || null;
    modalTitle.textContent = editingId ? "Editar cartão" : "Novo cartão";

    fTitle.value = cardOrDefaults?.title || "";
    fDesc.value  = cardOrDefaults?.desc || "";
    fTag.value   = cardOrDefaults?.tag || "";
    fDue.value   = cardOrDefaults?.due || "";
    fCol.value   = cardOrDefaults?.col || state.columns[0].id;

    modal.classList.add("show");
    fTitle.focus();
  }

  function closeModal(){
    modal.classList.remove("show");
    editingId = null;
  }

  document.getElementById("btnAdd").onclick = () => openModal({ col: state.columns[0].id });
  document.getElementById("btnCancel").onclick = closeModal;

  document.getElementById("btnSave").onclick = () => {
    const title = fTitle.value.trim();
    if(!title){ alert("Título é obrigatório."); return; }

    const payload = {
      col: fCol.value,
      title,
      desc: fDesc.value.trim(),
      tag: fTag.value.trim(),
      due: fDue.value
    };

    if(editingId){
      const c = state.cards.find(x => x.id === editingId);
      if(c) Object.assign(c, payload);
    }else{
      state.cards.push({ id: uid(), ...payload });
    }
    save();
    closeModal();
    render();
  };

  document.getElementById("btnAddCol").onclick = () => {
    const t = prompt("Nome da nova coluna:");
    if(!t || !t.trim()) return;
    state.columns.push({ id: uid(), title: t.trim() });
    save(); render();
  };

  document.getElementById("btnExport").onclick = async () => {
    const data = JSON.stringify(state, null, 2);
    try{
      await navigator.clipboard.writeText(data);
      alert("JSON copiado para a área de transferência.");
    }catch(e){
      alert("Não consegui copiar automaticamente. Vou abrir uma janela com o JSON.");
      const w = window.open();
      w.document.write("<pre>" + data.replaceAll("<","&lt;") + "</pre>");
    }
  };

  const modalImport = document.getElementById("modalImport");
  const importArea = document.getElementById("importArea");

  document.getElementById("btnImport").onclick = () => {
    importArea.value = "";
    modalImport.classList.add("show");
    importArea.focus();
  };
  document.getElementById("btnCancelImport").onclick = () => modalImport.classList.remove("show");

  document.getElementById("btnDoImport").onclick = () => {
    try{
      const s = JSON.parse(importArea.value);
      if(!s.columns || !s.cards) throw new Error("Formato inválido.");
      state = s;
      save();
      modalImport.classList.remove("show");
      render();
    }catch(e){
      alert("JSON inválido. Verifique o conteúdo e tente de novo.");
    }
  };

  document.getElementById("btnReset").onclick = () => {
    if(confirm("Resetar para o padrão? Isso apaga seu quadro atual.")){
      state = defaultState();
      save(); render();
    }
  };

  document.addEventListener("keydown", (e) => {
    if(e.key === "Escape"){
      modal.classList.remove("show");
      modalImport.classList.remove("show");
    }
  });

  render();
</script>
</body>
</html>
"""

def main():
    out = Path("kanban.html")
    out.write_text(HTML, encoding="utf-8")
    print(f"Arquivo criado: {out.resolve()}")
    print("Abra o kanban.html no navegador (clique duplo).")

if __name__ == "__main__":
    main()