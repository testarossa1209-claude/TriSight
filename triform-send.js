/* ===========================================================================
   triform-send.js — 各子システムからTriFormへ案件を渡すための共通ライブラリ
   2026-08-01 作成

   考え方：
     子システムはそれぞれ作りが違うので、送り方まで各自に書かせると
     形がばらける。ここに1本だけ置いて、どの子も同じ形で受信箱へ書く。
     受信箱（tritask_inbox）はTriForm・TriTaskと共有しているため、
     ここへ書けばTriFormの分解対象になり、TriTaskの一覧にも並ぶ。

   使い方（子システム側）：
     <script src="triform-send.js"></script>
     TriSightSend.send({
       source_product: "TriGrant®",
       program_name:   "キャリアアップ助成金（正社員化コース）",
       issuer:         "厚生労働省",
       summary:        "…",
       deadlines:      ["2026-09-30まで"],
       required_documents: [{name:"就業規則", note:"転換規定を含むこと"}],
       reverse_tasks:  [{due_text:"9月10日", action:"計画書を作る", must_verify:true}],
       verify_items:   [{item:"…", why:"…", contact:"…"}],
       contact:        "東京労働局"
     });
     TriSightSend.button(要素, ()=>payload, "TriFormへ送る");

   同じ制度名を再度送ったときは、新しい行を増やさず既存の行を更新する
   （何度も判定をやり直すたびに一覧が膨れるのを避けるため）。
   =========================================================================== */
(function(global){
  "use strict";

  var INBOX_KEY = "tritask_inbox";

  function authCode(){
    try{ return localStorage.getItem("trisight_access_code") || ""; }catch(e){ return ""; }
  }
  function companyName(){
    try{
      var c = JSON.parse(localStorage.getItem("trisight_dig_company") || "null");
      return (c && c["会社"] && c["会社"]["名称"]) || "";
    }catch(e){ return ""; }
  }
  function readInbox(){
    try{
      var a = JSON.parse(localStorage.getItem(INBOX_KEY) || "[]");
      return Array.isArray(a) ? a : [];
    }catch(e){ return []; }
  }
  function writeInbox(list){
    try{ localStorage.setItem(INBOX_KEY, JSON.stringify(list)); return true; }catch(e){ return false; }
  }

  /* 書類は文字列でも {name, note} でも受ける。子ごとに持ち方が違うため。 */
  function normDocs(docs){
    if(!docs) return [];
    return docs.map(function(d){
      if(typeof d === "string") return { name: d, note: "" };
      return { name: (d && d.name) || "", note: (d && d.note) || "", must_verify: !!(d && d.must_verify) };
    }).filter(function(d){ return d.name; });
  }
  function normTasks(tasks){
    if(!tasks) return [];
    return tasks.map(function(t){
      if(typeof t === "string") return { due_text:"", action:t, must_verify:false };
      return {
        due_text:(t && t.due_text) || "", action:(t && t.action) || "",
        must_verify: !!(t && t.must_verify),
        inputs:(t && t.inputs) || "",   /* 手元に要るもの */
        output:(t && t.output) || "",   /* この工程でできるもの */
        submit_to:(t && t.submit_to) || "", /* 持っていく先 */
        receive:(t && t.receive) || "",     /* 持ち帰るもの */
        why:(t && t.why) || "", from:(t && t.from) || ""
      };
    }).filter(function(t){ return t.action; });
  }
  function normVerify(items){
    if(!items) return [];
    return items.map(function(v){
      if(typeof v === "string") return { item:v, why:"", contact:"" };
      return { item:(v && v.item) || "", why:(v && v.why) || "", contact:(v && v.contact) || "" };
    }).filter(function(v){ return v.item; });
  }

  function send(payload){
    payload = payload || {};
    var name = payload.program_name || "（名称不明）";
    var code = authCode();
    var list = readInbox();

    /* 同じ認証コード・同じ制度名・同じ送付元は、増やさず上書きする */
    var idx = -1;
    for(var i = 0; i < list.length; i++){
      if(list[i] && list[i].program_name === name
         && (list[i].auth_code || "") === code
         && (list[i].source_product || "") === (payload.source_product || "")){ idx = i; break; }
    }

    var body = {
      source_product: payload.source_product || "（送付元不明）",
      program_name:   name,
      issuer:         payload.issuer || "",
      summary:        payload.summary || "",
      deadlines:      payload.deadlines || [],
      reverse_tasks:  normTasks(payload.reverse_tasks),
      required_documents: normDocs(payload.required_documents),
      verify_items:   normVerify(payload.verify_items),
      contact:        payload.contact || "",
      human_reviewed: false,
      updated_at:     new Date().toISOString()
    };

    var rec;
    if(idx >= 0){
      /* 進捗・実績・TriFormの分解結果は消さない。既に分解済みなら工程は上書きしない */
      var prev = list[idx];
      if(prev.triform_applied) delete body.reverse_tasks;
      rec = Object.assign({}, prev, body);
      list[idx] = rec;
    }else{
      rec = Object.assign({
        id: "TS-" + Date.now() + "-" + Math.floor(Math.random()*1000),
        created_at: new Date().toISOString(),
        auth_code: code,
        company_name: payload.company_name || companyName(),
        amount_expected: null,
        status: "未着手",
        paid_confirmed_at: null
      }, body);
      list.push(rec);
    }

    if(!writeInbox(list)) return { ok:false, reason:"保存できませんでした（保存容量の上限の可能性があります）" };
    return { ok:true, id:rec.id, updated: idx >= 0 };
  }

  /* 押すと送って、その場に結果を出すボタン。子システムの見た目に合わせて
     クラス名を渡せるようにしてある。 */
  function button(host, payloadFn, label, className){
    if(!host) return null;
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = label || "TriFormへ送る";
    if(className) b.className = className;
    else b.style.cssText = "margin-top:10px;padding:6px 14px;font-size:12.5px;cursor:pointer;"
       + "border:1px solid #c9772a;border-radius:7px;background:#fff;color:#c9772a;font-family:inherit";
    var note = document.createElement("span");
    note.style.cssText = "margin-left:10px;font-size:12px";
    b.addEventListener("click", function(){
      var r;
      try{ r = send(typeof payloadFn === "function" ? payloadFn() : payloadFn); }
      catch(e){ r = { ok:false, reason:String(e && e.message || e) }; }
      if(r.ok){
        note.style.color = "#3f7d57";
        note.textContent = r.updated
          ? "○ 既にある案件を更新しました。TriFormで開けます。"
          : "○ 送りました。TriFormを開くと工程に分解できます。";
      }else{
        note.style.color = "#8a2b2b";
        note.textContent = "× " + (r.reason || "送れませんでした");
      }
    });
    host.appendChild(b);
    host.appendChild(note);
    return b;
  }

  global.TriSightSend = { send: send, button: button, INBOX_KEY: INBOX_KEY };
})(window);
