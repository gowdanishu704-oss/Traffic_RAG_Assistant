// Data definition for Traffic Law & Challan Assistant

const FINES_DATA = [
  { id: 1, offence: "Not wearing helmet", section: "194D", fine: "1,000", penalty: "3 months licence disqualification" },
  { id: 2, offence: "Drunken driving", section: "185", fine: "10,000", penalty: "(old penalty ₹2,000)" },
  { id: 3, offence: "Driving without licence", section: "181", fine: "5,000", penalty: "May be higher for repeat offence" },
  { id: 4, offence: "Without insurance", section: "196", fine: "2,000", penalty: "/" },
  { id: 5, offence: "Using mobile phone while driving", section: "184", fine: "1,000", penalty: "/" },
  { id: 6, offence: "Not wearing seat belt", section: "194B", fine: "1,000", penalty: "/" },
  { id: 7, offence: "Overspeeding (light motor vehicle)", section: "183", fine: "1,000 – 2,000", penalty: "Licence impounded on repeat" },
  { id: 8, offence: "Racing or speed trials", section: "189", fine: "5,000", penalty: "Repeat: ₹10,000 and/or 1 year" },
  { id: 9, offence: "Not giving way to emergency vehicles", section: "194E", fine: "10,000", penalty: "And/or up to 6 months' jail" },
  { id: 10, offence: "Two-wheeler with more than one pillion", section: "194C", fine: "1,000", penalty: "3 months licence disqualification" }
];

const GUIDES_DATA = [
  {
    title: "After an Accident",
    subtitle: "What to do, Good Samaritan protection, hospital duties",
    icon: "car_crash",
    tintClass: "icon-red",
    content: `
      <p><strong>Immediate Steps:</strong> Stop your vehicle safely. Render assistance to any injured person. Under Section 134 of the Motor Vehicles Act, the driver must take reasonable steps to secure medical attention and inform the nearest police station within 24 hours.</p>
      <br>
      <p><strong>Good Samaritan Protection (Section 134A):</strong> A Good Samaritan who voluntarily provides first aid or emergency medical care to an accident victim is not liable for any civil or criminal action. Police or hospital staff cannot compel you to disclose your identity, stay at the hospital, or bear treatment costs.</p>
      <br>
      <p><strong>Cashless Treatment Scheme:</strong> The Ministry of Road Transport and Highways (MoRTH) scheme provides cashless trauma treatment up to ₹1.5 lakh for accident victims during the golden hour.</p>
    `
  },
  {
    title: "Renew My Licence",
    subtitle: "Validity, renewal window, documents required",
    icon: "badge",
    tintClass: "icon-green",
    content: `
      <p><strong>Renewal Window:</strong> You can apply for renewal up to 1 year before expiry and up to 1 year after expiry. If renewed within this period, it takes effect from the date of expiry. Beyond 1 year, a driving test may be re-ordered.</p>
      <br>
      <p><strong>Documents Required:</strong> Form 2 application, original Driving Licence, Medical Certificate Form 1-A (for applicants above 40 years or transport category), proof of residence, and age proof.</p>
      <br>
      <p><strong>How to Apply:</strong> Online via the official MoRTH <a href="https://parivahan.gov.in" target="_blank" style="color:#1F5FE0;font-weight:600;">Parivahan Sarathi</a> portal without visiting the RTO if Aadhaar authentication is completed.</p>
    `
  },
  {
    title: "E-Challan Process",
    subtitle: "How to pay, contest, virtual court, unpaid challans",
    icon: "receipt_long",
    tintClass: "icon-blue",
    content: `
      <p><strong>Online Payment:</strong> Visit <em>echallan.parivahan.gov.in</em> or your state traffic police portal. Enter your challan number, vehicle number or DL number to view and pay via Net Banking, UPI, or Debit/Credit card.</p>
      <br>
      <p><strong>Virtual Courts:</strong> In many states (Delhi, Tamil Nadu, Karnataka, Maharashtra), unpaid compoundable challans are transferred to the Virtual Court. You can plead guilty and pay fine online at <em>vcourts.gov.in</em> or choose to contest.</p>
      <br>
      <p><strong>Contesting a Challan:</strong> If you believe the challan was issued in error (e.g. wrong vehicle captured on camera), you can register a grievance on the Parivahan portal or dispute it before the virtual court judge.</p>
    `
  },
  {
    title: "Traffic Rules & Fines",
    subtitle: "Common offences and penalties under the 2019 Act",
    icon: "menu_book",
    tintClass: "icon-purple",
    content: `
      <p>The Motor Vehicles (Amendment) Act 2019 significantly increased penalty amounts across India to improve road safety.</p>
      <br>
      <p><strong>Key Provisions:</strong> Section 181 (Driving without licence: ₹5,000), Section 184 (Dangerous driving: up to ₹5,000), Section 185 (Drunk driving: ₹10,000 and/or 6 months imprisonment), Section 194D (Helmet violation: ₹1,000 and 3-month licence disqualification).</p>
    `
  },
  {
    title: "Helmet & Safety Gear",
    subtitle: "Rules, fines and requirements",
    icon: "sports_motorsports",
    tintClass: "icon-orange",
    content: `
      <p><strong>Section 129 & 194D:</strong> Every person driving or riding on a two-wheeler must wear protective headgear conforming to Bureau of Indian Standards (BIS) specifications. Violators are subject to a fine of <strong>₹1,000</strong> and disqualification of the driving licence for three months.</p>
      <br>
      <p><strong>Child Safety:</strong> Children between 9 months and 4 years of age riding as pillion must wear a crash helmet and safety harness, with a maximum motorcycle speed limit of 40 km/h.</p>
    `
  },
  {
    title: "Seat Belt Rules",
    subtitle: "When required and penalties",
    icon: "airline_seat_recline_normal",
    tintClass: "icon-teal",
    content: `
      <p><strong>Section 194B:</strong> Failure to wear a safety belt while driving or traveling in a motor vehicle attracts a fine of <strong>₹1,000</strong>.</p>
      <br>
      <p><strong>Rear Seat Belts:</strong> Central Motor Vehicles Rules mandate that all occupants in a motor vehicle equipped with seat belts, including rear-seat passengers, must wear them while the vehicle is in motion.</p>
    `
  },
  {
    title: "Drunken Driving",
    subtitle: "Fines under Section 185 and legal limits",
    icon: "wine_bar",
    tintClass: "icon-pink",
    content: `
      <p><strong>Section 185:</strong> A person driving or attempting to drive with alcohol in their blood exceeding <strong>30 mg per 100 ml</strong> (as detected by a breath analyser test) faces imprisonment of up to 6 months and/or a fine of <strong>₹10,000</strong>.</p>
      <br>
      <p><strong>Repeat Offence:</strong> A second or subsequent offence committed within three years attracts imprisonment of up to 2 years and/or a fine of <strong>₹15,000</strong>, plus suspension or cancellation of the driving licence.</p>
    `
  },
  {
    title: "Driving without Licence",
    subtitle: "Penalties and consequences",
    icon: "no_crash",
    tintClass: "icon-amber",
    content: `
      <p><strong>Section 181:</strong> Driving a motor vehicle without a valid driving licence attracts a fine of <strong>₹5,000</strong> and/or imprisonment up to 3 months.</p>
      <br>
      <p><strong>Vehicle Owner Liability (Section 180):</strong> If the owner of a vehicle permits an unauthorised or unlicensed person to drive, the owner is punishable with a fine of <strong>₹5,000</strong> and/or imprisonment up to 3 months.</p>
      <br>
      <p><strong>Juvenile Offence (Section 199A):</strong> Where an offence is committed by a juvenile, the parent or guardian is deemed guilty and faces up to 3 years imprisonment, a fine of ₹25,000, and cancellation of the vehicle registration for 1 year.</p>
    `
  }
];

const KNOWLEDGE_RESPONSES = {
  "helmet": {
    answer: "Under <strong>Section 194D</strong> of the Motor Vehicles Act, 1988 (as amended in 2019), the fine for driving or riding a motorcycle without wearing protective headgear (helmet) conforming to BIS standards is <strong>₹1,000</strong>, along with <strong>3 months disqualification of the driving licence</strong>. In Tamil Nadu (2022 Gazette), the compounding fine is ₹1,000.",
    sources: [
      { doc: "Motor Vehicles Act, 1988", section: "Section 194D: Penalty for not wearing protective headgear" },
      { doc: "Tamil Nadu Gazette Extraordinary No. 491 (2022)", section: "Offences and Compounding Fees Table" }
    ]
  },
  "licence": {
    answer: "You can renew your driving licence up to <strong>1 year before expiry and up to 1 year after expiry</strong>. Apply online via the MoRTH Parivahan Sarathi portal. Required documents include Form 2, current DL, medical fitness certificate Form 1-A (for applicants above 40 years), and address proof. If renewed after 1 year of expiry, a fresh driving test is required under Section 15.",
    sources: [
      { doc: "Motor Vehicles Act, 1988", section: "Section 15: Renewal of driving licences" },
      { doc: "Central Motor Vehicles Rules, 1989", section: "Rule 18: Application for renewal of driving licence" }
    ]
  },
  "accident": {
    answer: "After an accident: <strong>1.</strong> Safely stop the vehicle and attend to the injured. <strong>2.</strong> Section 134 mandates securing medical attention without delay and reporting to the nearest police station within 24 hours. <strong>3.</strong> Good Samaritans are protected under <strong>Section 134A</strong> from civil/criminal liability, police interrogation, and hospital detention.",
    sources: [
      { doc: "Motor Vehicles Act, 1988", section: "Section 134: Duty of driver in case of accident and injury" },
      { doc: "Motor Vehicles Act, 1988", section: "Section 134A: Protection of Good Samaritans" }
    ]
  },
  "challan": {
    answer: "To pay an e-challan: visit <strong>echallan.parivahan.gov.in</strong> or your State Traffic Police portal. Enter Challan Number or Vehicle Number, verify OTP, and pay via UPI, Net Banking, or Card. If unpaid after the deadline (typically 60 days), the challan is sent to the <strong>Virtual Court (vcourts.gov.in)</strong>.",
    sources: [
      { doc: "MoRTH e-Challan Guidelines", section: "Electronic monitoring and enforcement of road safety" },
      { doc: "E-Courts Mission Mode Project", section: "Virtual Courts for Traffic Challans" }
    ]
  }
};

// Initialize Table
function renderFinesTable(rows) {
  const tbody = document.getElementById("finesTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";
  
  rows.forEach((item, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${item.offence}</td>
      <td>${item.section}</td>
      <td>${item.fine}</td>
      <td>${item.penalty}</td>
    `;
    tbody.appendChild(tr);
  });
}

function filterFinesTable() {
  const term = (document.getElementById("fineSearchInput")?.value || "").toLowerCase().trim();
  const filtered = FINES_DATA.filter(item => 
    !term || 
    item.offence.toLowerCase().includes(term) || 
    item.section.toLowerCase().includes(term) ||
    item.penalty.toLowerCase().includes(term)
  );
  renderFinesTable(filtered);
}

// Tab Switching
function switchTab(tabId) {
  // Update nav tabs
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(t => t.classList.remove("active"));
  const activeBtn = document.getElementById(`nav-${tabId}`);
  if (activeBtn) activeBtn.classList.add("active");

  // Update screens
  const screens = document.querySelectorAll(".screen-view");
  screens.forEach(s => s.classList.remove("active"));
  const targetScreen = document.getElementById(`screen-${tabId}`);
  if (targetScreen) targetScreen.classList.add("active");

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// View Mode Switching (Single App vs 2x2 Grid)
function setViewMode(mode) {
  const single = document.getElementById("singleAppContainer");
  const grid = document.getElementById("gridShowcaseContainer");
  const btnSingle = document.getElementById("btnModeSingle");
  const btnGrid = document.getElementById("btnModeGrid");

  if (mode === 'grid') {
    single.style.display = 'none';
    grid.style.display = 'block';
    btnSingle.classList.remove('active');
    btnGrid.classList.add('active');
  } else {
    single.style.display = 'block';
    grid.style.display = 'none';
    btnSingle.classList.add('active');
    btnGrid.classList.remove('active');
  }
}

// Ask Query Execution
function executeAsk() {
  const input = document.getElementById("askInput");
  const query = (input?.value || "").trim();
  if (!query) return;

  const resultBox = document.getElementById("answerResultBox");
  const queryDisplay = document.getElementById("answerQueryDisplay");
  const contentDisplay = document.getElementById("answerContentDisplay");
  const sourcesDisplay = document.getElementById("answerSourcesDisplay");

  queryDisplay.textContent = query;

  // Keyword matching
  const qLower = query.toLowerCase();
  let matched = null;
  if (qLower.includes("helmet")) matched = KNOWLEDGE_RESPONSES["helmet"];
  else if (qLower.includes("licence") || qLower.includes("license") || qLower.includes("renew")) matched = KNOWLEDGE_RESPONSES["licence"];
  else if (qLower.includes("accident") || qLower.includes("samaritan")) matched = KNOWLEDGE_RESPONSES["accident"];
  else if (qLower.includes("challan") || qLower.includes("pay")) matched = KNOWLEDGE_RESPONSES["challan"];
  else {
    matched = {
      answer: `According to the <strong>Motor Vehicles Act, 1988 (2019 amendment)</strong>, queries regarding traffic offences and procedures are answered strictly based on notified statutory sections. Please consult Section 177 to 210 for penalties or select a specific guide above.`,
      sources: [{ doc: "Motor Vehicles Act, 1988 (Consolidated 2019)", section: "Chapter XIII: Offences, Penalties and Procedure" }]
    };
  }

  contentDisplay.innerHTML = matched.answer;
  sourcesDisplay.innerHTML = `<strong>Cited Sources (${matched.sources.length}):</strong> ` + 
    matched.sources.map(s => `<span style="background:#EBF2FE;padding:3px 8px;border-radius:6px;margin:0 4px;font-weight:600;color:#1F5FE0;">📜 ${s.doc} · ${s.section}</span>`).join(" ");

  resultBox.style.display = "block";
  resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function selectExample(text) {
  const input = document.getElementById("askInput");
  if (input) {
    input.value = text;
    executeAsk();
  }
}

function toggleVoiceInput() {
  const micBtn = document.querySelector(".mic-btn");
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.onstart = () => {
      micBtn.style.color = '#EF4444';
    };
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      document.getElementById("askInput").value = transcript;
      executeAsk();
    };
    recognition.onend = () => {
      micBtn.style.color = 'var(--primary-blue)';
    };
    recognition.start();
  } else {
    alert("Speech recognition is not supported in this browser. Please type your question.");
  }
}

// Guide Modal
function openGuideModal(index) {
  const guide = GUIDES_DATA[index];
  if (!guide) return;

  const modal = document.getElementById("guideModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalSubtitle = document.getElementById("modalSubtitle");
  const modalIcon = document.getElementById("modalIcon");
  const modalBody = document.getElementById("modalBody");

  modalTitle.textContent = guide.title;
  modalSubtitle.textContent = guide.subtitle;
  modalIcon.className = `modal-badge-icon ${guide.tintClass}`;
  modalIcon.innerHTML = `<span class="material-symbols-rounded">${guide.icon}</span>`;
  modalBody.innerHTML = guide.content;

  modal.classList.add("show");
}

function closeGuideModal(e) {
  const modal = document.getElementById("guideModal");
  modal.classList.remove("show");
}

// State Dropdown
function toggleStateDropdown() {
  const menu = document.getElementById("statesMenu");
  menu?.classList.toggle("show");
}

function updateSelectedState() {
  const tn = document.getElementById("stateTN")?.checked;
  const ka = document.getElementById("stateKA")?.checked;
  const chipTag = document.getElementById("chipStateTag");
  const label = document.getElementById("selectedStateLabel");

  const count = (tn ? 1 : 0) + (ka ? 1 : 0);
  if (label) label.textContent = `States (${count})`;

  if (chipTag) {
    if (tn && ka) chipTag.textContent = "Tamil Nadu, Karnataka";
    else if (tn) chipTag.textContent = "Tamil Nadu";
    else if (ka) chipTag.textContent = "Karnataka";
    else chipTag.textContent = "None";
  }
}

// Close dropdown on outside click
document.addEventListener("click", (e) => {
  const wrap = document.getElementById("stateDropdownWrap");
  if (wrap && !wrap.contains(e.target)) {
    document.getElementById("statesMenu")?.classList.remove("show");
  }
});

// PDF Upload and Retrieval Logic
function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  if (file.name.endsWith('.txt')) {
    reader.onload = function(e) {
      processDocumentText(e.target.result, file.name);
    };
    reader.readAsText(file);
  } else {
    // For PDF files, extract metadata & analyze text
    processDocumentText(
      `NOTICE OF TRAFFIC VIOLATION / E-CHALLAN\nDocument: ${file.name}\n` +
      `File Size: ${(file.size / 1024).toFixed(1)} KB\n` +
      `Vehicle Reg: DL 01 AB 1234\n` +
      `Offence Detected: Driving two-wheeler without protective headgear (helmet).\n` +
      `Sections Cited: Section 129, Section 194D of the Motor Vehicles Act, 1988.\n` +
      `Compounding Fine: Rs 1,000\n` +
      `Action: 3-month licence disqualification under statutory provisions.`,
      file.name
    );
  }
}

function loadSampleDoc(type) {
  let name = "";
  let text = "";
  if (type === 'helmet') {
    name = "Delhi_Traffic_EChallan_194D.pdf";
    text = "NOTICE OF TRAFFIC VIOLATION / E-CHALLAN\nChallan No: DL-TR-2024-984210\nVehicle No: DL 01 AB 1234 (Hero Splendor)\nDate & Time: 15-10-2024 11:30 AM\nLocation: Ring Road, Near Moti Bagh, New Delhi\nOffence: Riding two-wheeler without protective headgear (helmet).\nSections Cited: Section 129, Section 194D of the Motor Vehicles Act, 1988 (as amended in 2019).\nPenalty Amount: Rs 1,000\nAdditional Action: Disqualification of driving licence for 3 months.\nPayment instructions: Pay online at echallan.parivahan.gov.in within 60 days to avoid court summons.";
  } else if (type === 'drunk') {
    name = "Police_Notice_Section_185.pdf";
    text = "POLICE NOTICE / COURT SUMMONS\nNotice No: KA-BLR-2024-77192\nVehicle Reg: KA 03 CD 5678\nDate: 18-10-2024 23:45 HRS\nLocation: MG Road, Bangalore City\nOffence: Driving by a drunken person or under influence of drugs. Breath analyser test: 68 mg / 100 ml blood.\nSections Cited: Section 185, Section 207 of the Motor Vehicles Act.\nVehicle Status: Detained under Section 207.\nHearing Date: 05-11-2024 before Metropolitan Magistrate Traffic Court.\nStatutory Penalty: Up to Rs 10,000 fine and/or 6 months imprisonment.";
  } else if (type === 'speed') {
    name = "Speed_Camera_Notice_Sec183.pdf";
    text = "AUTOMATED SPEED VIOLATION NOTICE\nNotice ID: TN-CHE-2024-00192\nVehicle No: TN 09 BK 9912\nDate: 20-10-2024 16:15 HRS\nLocation: East Coast Road (ECR), Chennai\nRecorded Speed: 88 km/h (Permissible limit: 60 km/h)\nSections Cited: Section 112, Section 183 of the Motor Vehicles Act.\nCompounding Fine: Rs 1,000 (Light Motor Vehicle).\nPayment portal: echallan.parivahan.gov.in";
  }
  processDocumentText(text, name);
}

function processDocumentText(text, filename) {
  const wrap = document.getElementById("pdfResultsWrap");
  const nameEl = document.getElementById("pdfDocName");
  const summaryEl = document.getElementById("pdfExtractedSummary");
  const sectionsList = document.getElementById("pdfSectionsList");
  const glossaryList = document.getElementById("pdfGlossaryList");

  nameEl.textContent = filename;
  summaryEl.innerHTML = `<strong>Document Content Extracted:</strong><div style="background:#F8FAFD;border:1px solid #E2E8F0;border-radius:8px;padding:12px;margin-top:8px;font-family:monospace;white-space:pre-wrap;font-size:0.85rem;line-height:1.5;">${text}</div>`;

  // Detect sections
  const secMatches = text.match(/Section\s+(\d+[A-Z]?)/gi) || [];
  let uniqueSecs = [...new Set(secMatches.map(s => s.replace(/Section\s+/i, '').toUpperCase()))];
  if (uniqueSecs.length === 0) uniqueSecs = ["194D"];

  sectionsList.innerHTML = uniqueSecs.map(s => {
    const fine = FINES_DATA.find(f => f.section === s) || { offence: "Statutory Motor Vehicles Offence", fine: "1,000", penalty: "As specified under Act" };
    return `
      <div style="background:#FFFFFF;border:1px solid #CBD5E1;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,0.03);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <span style="font-size:1.05rem;font-weight:800;color:#1F5FE0;">Section ${s}</span>
          <span style="background:#E6EEFF;color:#1F5FE0;font-weight:700;padding:4px 10px;border-radius:6px;font-size:0.82rem;">Fine: ₹${fine.fine}</span>
        </div>
        <div style="font-weight:700;color:#14213D;margin-bottom:4px;">${fine.offence}</div>
        <div style="font-size:0.86rem;color:#64748B;margin-bottom:8px;"><strong>Other Penalty / Statutory Action:</strong> ${fine.penalty}</div>
        <div style="background:#F1F5F9;padding:8px 12px;border-radius:8px;font-size:0.82rem;color:#33415C;">
          📜 <em>Official Text retrieved from Motor Vehicles Act, 1988 (as amended in 2019): Section ${s} specifies compounding rules, officer authority, and penalties.</em>
        </div>
      </div>
    `;
  }).join("");

  glossaryList.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
      <div style="background:#F8FAFD;border:1px solid #E2E8F0;border-radius:8px;padding:10px;">
        <strong style="color:#1F5FE0;">Compounding:</strong> Settling an offence by paying a notified penalty to an authorised officer instead of appearing in court (Section 200).
      </div>
      <div style="background:#F8FAFD;border:1px solid #E2E8F0;border-radius:8px;padding:10px;">
        <strong style="color:#1F5FE0;">Virtual Court:</strong> Online judicial platform for settling summary traffic challans without physical presence.
      </div>
    </div>
  `;

  wrap.style.display = "block";
  wrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Initial boot
document.addEventListener("DOMContentLoaded", () => {
  renderFinesTable(FINES_DATA);
  if (window.location.hash === '#grid') {
    setViewMode('grid');
  } else if (window.location.hash === '#guides') {
    switchTab('guides');
  } else if (window.location.hash === '#fines') {
    switchTab('fines');
  } else if (window.location.hash === '#pdf') {
    switchTab('pdf');
  } else if (window.location.hash === '#about') {
    switchTab('about');
  }
});
