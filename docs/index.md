<link rel="stylesheet" href="css/normalize.css" />
<link rel="stylesheet" href="css/fonts.css" />
<link rel="stylesheet" href="css/styles.css" />
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.min.css" crossorigin="anonymous" />

<style>
/* Only target navigation bar to keep it untouched */
body {
  --md-primary-fg-color: var(--md-primary-fg-color);
}

/* Hide Material theme page title */
header.md-header-nav__title {
  display: none !important;
}

/* Remove sidebars but keep good spacing */
.md-sidebar {
  display: none !important;
  width: 0 !important;
}

/* Set reasonable content area spacing */
.md-main__inner {
  max-width: 100% !important;
  margin: 0 auto !important;
}

.md-content {
  max-width: 100% !important;
  margin: 0 auto !important;
}

.md-content__inner {
  max-width: 100% !important;
  padding: 1rem 1.5rem !important;
}

/* Content wrapper styles */
.content-wrapper {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

.content-box {
  border-radius: 5px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
  padding: 20px;
  width: 100%;
}

.leaderboard {
  overflow-x: auto;
}

.tab {
  list-style-type: none;
  margin: 0;
  padding: 0;
  overflow: hidden;
  border-bottom: 1px solid #ccc;
  display: flex;
}

.tab li {
  float: left;
}

.tablinks {
  display: inline-block;
  background-color: inherit;
  padding: 10px 16px;
  transition: 0.3s;
  font-size: 17px;
  border: none;
  cursor: pointer;
}

.tablinks:hover {
  background-color: #ddd;
}

.tablinks.active {
  background-color: var(--dark_accent_color);
  color: white;
}

.tabcontent {
  display: none;
  padding: 6px 12px;
  border-top: none;
  overflow-x: auto; /* Ensure horizontal scrolling works */
}

.table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px; /* Ensure table doesn't shrink too much */
}

.table th, .table td {
  padding: 8px;
  text-align: center;
  border-bottom: 1px solid #ddd;
}

.table th {
  position: sticky;
  top: 0;
  background-color: inherit;
  z-index: 10;
}

.sticky-header-content {
  padding: 10px 0;
  font-weight: bold;
  text-align: center;
}

.model-type {
  margin: 0;
  text-align: left;
}

.number {
  text-align: center;
  margin: 0;
}

.label-date {
  white-space: nowrap;
}

.scrollable {
  overflow-x: auto;
}

/* Style for download buttons to work with any background */
.download {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 8px 12px;
  margin-bottom: 8px;
  transition: all 0.2s ease;
}

.download:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

/* Essential styles for the leaderboard */
:root {
  --dark_accent_color: #005587;
}
</style>

<!-- Leaderboard Component -->
<div class="content-wrapper">
  <div class="content-box leaderboard">
    <ul class="tab">
      <li><button id="tab-lite" class="tablinks" data-leaderboard="Lite" style="display: flex; align-items: center;">Lite</button></li>
      <li><button id="tab-verified" class="tablinks" data-leaderboard="Verified" style="display: flex; align-items: center;">Verified</button></li>
      <li><button id="tab-test" class="tablinks" data-leaderboard="Test" style="display: flex; align-items: center;">Full</button></li>
      <li><button id="tab-multimodal" class="tablinks" data-leaderboard="Multimodal" style="display: flex; align-items: center;">Multimodal</button></li>
    </ul>
    <div class="tabcontent" id="leaderboard-Test">
      <table class="table scrollable">
        <thead>
          <tr>
            <th><div class="sticky-header-content">Model</div></th>
            <th><div class="sticky-header-content">% Resolved</div></th>
            <th><div class="sticky-header-content">Org</div></th>
            <th><div class="sticky-header-content">Date</div></th>
            <th><div class="sticky-header-content">Logs</div></th>
            <th><div class="sticky-header-content">Trajs</div></th>
            <th><div class="sticky-header-content">Site</div></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p class="model-type">🆕 🥇 🤠 ✅ SWE-agent 1.0 (Claude 3.7 Sonnet)</p>
            </td>
            <td><p class="number">33.83</p></td>
            <td>
              <p style="display: flex; justify-content: center; align-items: center;">-</p>
            </td>
            <td><p><span class="label-date">2025-02-27</span></p></td>
            <td><p style="text-align: center;">✓</p></td>
            <td><p style="text-align: center;">✓</p></td>
            <td>
              <p style="text-align: center;">
                <a href="https://github.com/swe-agent/swe-agent">🔗</a>
              </p>
            </td>
          </tr>
          <!-- More rows would go here -->
        </tbody>
      </table>
    </div>
    <div class="tabcontent" id="leaderboard-Verified">
      <!-- Verified tab content -->
      <table class="table scrollable">
        <thead>
          <tr>
            <th><div class="sticky-header-content">Model</div></th>
            <th><div class="sticky-header-content">% Resolved</div></th>
            <th><div class="sticky-header-content">Org</div></th>
            <th><div class="sticky-header-content">Date</div></th>
            <th><div class="sticky-header-content">Logs</div></th>
            <th><div class="sticky-header-content">Trajs</div></th>
            <th><div class="sticky-header-content">Site</div></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p class="model-type">🆕 🥇 Augment Agent v0</p>
            </td>
            <td><p class="number">65.40</p></td>
            <td>
              <p style="display: flex; justify-content: center; align-items: center;">
                <img src="https://augment-assets.com/augmentcode-mark-green.png" style="height: 1.25em;" />
              </p>
            </td>
            <td><p><span class="label-date">2025-03-16</span></p></td>
            <td><p style="text-align: center;">✓</p></td>
            <td><p style="text-align: center;">✓</p></td>
            <td>
              <p style="text-align: center;">
                <a href="https://www.augmentcode.com">🔗</a>
              </p>
            </td>
          </tr>
          <!-- More rows would go here -->
        </tbody>
      </table>
    </div>
    <div class="tabcontent" id="leaderboard-Lite">
      <!-- Lite tab content -->
      <table class="table scrollable">
        <thead>
          <tr>
            <th><div class="sticky-header-content">Model</div></th>
            <th><div class="sticky-header-content">% Resolved</div></th>
            <th><div class="sticky-header-content">Org</div></th>
            <th><div class="sticky-header-content">Date</div></th>
            <th><div class="sticky-header-content">Logs</div></th>
            <th><div class="sticky-header-content">Trajs</div></th>
            <th><div class="sticky-header-content">Site</div></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p class="model-type">🥇 Isoform</p>
            </td>
            <td><p class="number">55.00</p></td>
            <td>
              <p style="display: flex; justify-content: center; align-items: center;">
                <img src="https://avatars.githubusercontent.com/u/4956703?s=200&v=4" style="height: 1.25em;" />
              </p>
            </td>
            <td><p><span class="label-date">2025-01-14</span></p></td>
            <td><p style="text-align: center;">✓</p></td>
            <td><p style="text-align: center;">✓</p></td>
            <td>
              <p style="text-align: center;">
                <a href="https://www.isoform.ai">🔗</a>
              </p>
            </td>
          </tr>
          <!-- More rows would go here -->
        </tbody>
      </table>
    </div>
    <div class="tabcontent" id="leaderboard-Multimodal">
      <!-- Multimodal tab content -->
      <table class="table scrollable">
        <thead>
          <tr>
            <th><div class="sticky-header-content">Model</div></th>
            <th><div class="sticky-header-content">% Resolved</div></th>
            <th><div class="sticky-header-content">Org</div></th>
            <th><div class="sticky-header-content">Date</div></th>
            <th><div class="sticky-header-content">Logs</div></th>
            <th><div class="sticky-header-content">Trajs</div></th>
            <th><div class="sticky-header-content">Site</div></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p class="model-type">🆕 🥇 ✅ Globant Code Fixer Agent</p>
            </td>
            <td><p class="number">29.59</p></td>
            <td>
              <p style="display: flex; justify-content: center; align-items: center;">
                <img src="https://ai.globant.com/wp-content/uploads/2024/06/favicon.png" style="height: 1.25em;" />
              </p>
            </td>
            <td><p><span class="label-date">2025-03-25</span></p></td>
            <td><p style="text-align: center;">-</p></td>
            <td><p style="text-align: center;">-</p></td>
            <td>
              <p style="text-align: center;">
                <a href="https://ai.globant.com/us-en/">🔗</a>
              </p>
            </td>
          </tr>
          <!-- More rows would go here -->
        </tbody>
      </table>
    </div>
    <p>
      SWE-bench <b>Lite</b> is a subset of SWE-bench that's been curated to make evaluation less costly and more accessible.
      <br>
      SWE-bench <b>Verified</b> is a human annotator filtered subset that has been deemed to have a ceiling of 100% resolution rate.
      <br>
      SWE-bench <b>Multimodal</b> is a new dataset featuring issues with visual elements (images, videos) from JavaScript repositories.
      <br><br>
      - The <span style="color:#0ea7ff;"><b>% Resolved</b></span> metric is the percentage of instances
      (<b>2294</b> for test, <b>500</b> for verified, <b>300</b> for lite, <b>517</b> for Multimodal) <i>solved</i> by the model.
      <br>
      - <span style="color:#0ea7ff;"><b>✅ Checked</b></span> indicates that we, the SWE-bench team, received access to the system and
      were able to reproduce the patch generations.
      <br>
      - <span style="color:#0ea7ff;"><b>🤠 Open</b></span> refers to submissions that have open-source code. This does <i>not</i>
      necessarily mean the underlying model is open-source.
      <br>
      - <span style="color:#0ea7ff;"><b>🆕 New</b></span> refers to the most recently submitted solutions.
    </p>
  </div>
</div>

<!-- News Section -->
<div class="content-wrapper" style="display: flex; justify-content: center; align-items: center;">
  <div class="content-box">
    <h2 class="text-title">News</h2>
    <p style="margin-bottom: 0.5em">
      📣 [10/2024] Introducing <b>SWE-bench Multimodal</b>! Can AI systems "see" bugs and fix them? 👀 💻
      [<a style="color:#0ca7ff" href="multimodal.html">Link</a>]
    </p>
    <p style="margin-bottom: 0.5em">
      📣 [08/2024] SWE-bench x OpenAI = <b>SWE-bench Verified</b>, a human-validated subset of
      500 problems reviewed by software engineers!
      [<a style="color:#0ca7ff" href="https://openai.com/index/introducing-swe-bench-verified/">Report</a>]
    </p>
    <p style="margin-bottom: 0.5em">
      📣 [06/2024] We've <b>Docker</b>-ized SWE-bench for easier, containerized, reproducible evaluation.
      [<a style="color:#0ca7ff" href="https://github.com/swe-bench/SWE-bench/tree/main/docs/20240627_docker">Report</a>]
    </p>
    <p style="margin-bottom: 0.5em">
      📣 [03/2024] Check out our latest work, <b>SWE-agent</b>, which achieves a 12.47% resolve rate on SWE-bench!
      [<a href="https://github.com/princeton-nlp/SWE-agent" class="light-blue-link" target="_blank" rel="noopener noreferrer">Link</a>]
    </p>
    <p style="margin-bottom: 0.5em">
      📣 [03/2024] We've released <b>SWE-bench Lite</b>! Running all of SWE-bench can take time. This subset makes it easier!
      [<a style="color:#0ca7ff" href="lite.html">Report</a>]
    </p>
  </div>
</div>

<!-- Resources Section -->
<div class="content-wrapper">
  <div class="content-box">
    <h2 class="text-title">Resources</h2>
    <p class="text-content">
      You can download the SWE-bench task instances from HuggingFace or directly as a JSON
      file (<a href="https://drive.google.com/uc?export=download&id=1SbOxHiR0eXlq2azPSSOIDZz-Hva0ETpX">development</a>,
      <a href="https://drive.google.com/uc?export=download&id=164g55i3_B78F6EphCZGtgSrd2GneFyRM">test</a> sets).
      For your convenience, to fine tune your own model for evaluation on SWE-bench, we provide five pre-processed datasets at different retrieval settings ("Oracle", 13K, 27K, 40K, 50K "Llama"). We recommend using the 13K, 27K, or 40K datasets for evaluation. The 50K "Llama" dataset is provided for reproducing the results of the SWE-bench paper.
    </p>
    <div class="content-wrapper" style="width: 100%">
      <div class="content-box column">
        <a
          style="width: 100%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench"
        >
          <div class="download">🤗 SWE-bench</div>
        </a>
        <a
          style="width: 100%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_oracle"
        >
          <div class="download">
            🤗 "Oracle" Retrieval
          </div>
        </a>
        <a
        style="width: 100%"
        href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_bm25_50k_llama"
      >
        <div class="download">
          🤗 BM25 Retrieval 50K (Llama)
        </div>
      </a>
      </div>
      <div class="content-box column">
        <a
          style="width: 100%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_bm25_13K"
        >
          <div class="download">
            🤗 BM25 Retrieval 13K
          </div>
        </a>
        <a
          style="width: 100%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_bm25_27K"
        >
          <div class="download">
            🤗 BM25 Retrieval 27K
          </div>
        </a>
        <a
          style="width: 100%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_bm25_40K"
        >
          <div class="download">
            🤗 BM25 Retrieval 40K
          </div>
        </a>
      </div>
    </div>
    <p class="text-content" style="margin-top:1em;">
      SWE-bench Lite is also available for download from HuggingFace.
    </p>
    <div class="content-wrapper" style="width: 100%">
      <div class="content-box column">
        <a
          style="width: 100%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite"
        >
          <div class="download">🤗 SWE-bench Lite</div>
        </a>
        <a
          style="width: 100%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite_oracle"
        >
          <div class="download">
            🤗 "Oracle" Retrieval Lite
          </div>
        </a>
      </div>
      <div class="content-box column">
        <a
          style="width: 100%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite_bm25_13K"
        >
          <div class="download">
            🤗 BM25 Retrieval 13K Lite
          </div>
        </a>
        <a
          style="width: 100%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite_bm25_27K"
        >
          <div class="download">
            🤗 BM25 Retrieval 27K Lite
          </div>
        </a>
      </div>
    </div>
    <p class="text-content" style="margin-top:1em;">
      SWE-bench Verified can be downloaded from HuggingFace.
    </p>
    <div class="content-wrapper" style="width: 100%">
      <div class="content-box column">
        <a
          style="width: 50%"
          href="https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified"
        >
          <div class="download">🤗 SWE-bench Verified</div>
        </a>
      </div>
    </div>
    <p class="text-content" style="margin-top:1em;">
      We also provide the full SWE-Llama model weights at 13b and 7b parameters, along with their PEFT LoRA weights.
    </p>
    <div class="content-wrapper" style="width: 100%">
      <div class="content-box column">
        <a
          style="width: 100%"
          href="https://huggingface.co/princeton-nlp/SWE-Llama-13b"
        >
          <div class="download">
            <img
              src="img/swellama.png"
              style="height:1.3em;vertical-align: middle;margin-bottom:0.35em;margin-right:0.2em;background-color: var(--dark_accent_color)"
            />
            SWE-Llama 13b
          </div>
        </a>
        <a
          style="width: 100%"
          href="https://huggingface.co/princeton-nlp/SWE-Llama-13b-peft"
        >
          <div class="download">
            <img
              src="img/swellama.png"
              style="height:1.3em;vertical-align: middle;margin-bottom:0.35em;margin-right:0.2em;background-color: var(--dark_accent_color)"
            />
            SWE-Llama 13b (PEFT)
          </div>
        </a>
      </div>
      <div class="content-box column">
        <a
          style="width: 100%"
          href="https://huggingface.co/princeton-nlp/SWE-Llama-7b"
        >
          <div class="download">
            <img
              src="img/swellama.png"
              style="height:1.3em;vertical-align: middle;margin-bottom:0.35em;margin-right:0.2em;background-color: var(--dark_accent_color)"
            />
            SWE-Llama 7b
          </div>
        </a>
        <a
          style="width: 100%"
          href="https://huggingface.co/princeton-nlp/SWE-Llama-7b-peft"
        >
          <div class="download">
            <img
              src="img/swellama.png"
              style="height:1.3em;vertical-align: middle;margin-bottom:0.35em;margin-right:0.2em;background-color: var(--dark_accent_color)"
            />
            SWE-Llama 7b (PEFT)
          </div>
        </a>
      </div>
    </div>
  </div>
</div>

<!-- About Section -->
<div class="content-wrapper">
  <div class="content-box">
    <h2 class="text-title">About</h2>
    <img src="img/teaser.png" style="width:80%;margin:auto;display:block;"/>
    <p class="text-content">
      SWE-bench is a dataset that tests systems' ability to solve GitHub
      issues automatically. The dataset collects 2,294 Issue-Pull Request
      pairs from 12 popular Python repositories. Evaluation is performed by unit test verification using post-PR behavior as the reference solution.
      Read more about SWE-bench in our <a href="https://arxiv.org/abs/2310.06770", target="_blank">paper</a>!
    </p class="text-content">
    <h3 class="text-title" style="margin-bottom:0.5em">Citation</h3>
    <pre id="citation"><code>@inproceedings{
    jimenez2024swebench,
    title={{SWE}-bench: Can Language Models Resolve Real-world Github Issues?},
    author={Carlos E Jimenez and John Yang and Alexander Wettig and Shunyu Yao and Kexin Pei and Ofir Press and Karthik R Narasimhan},
    booktitle={The Twelfth International Conference on Learning Representations},
    year={2024},
    url={https://openreview.net/forum?id=VTF8yNQM66}
}</code></pre>
    <p class="text-content" style="margin-bottom: 0;">
      <b>Disclaimer:</b> SWE-bench is for research purposes only. Models
      trained and evaluated on SWE-bench can produce unexpected results.
      We are not responsible for any damages caused by the use of
      SWE-bench, including but not limited to, any loss of profit, data,
      or use of data.
    <p style="line-height: 1.6667em;">
      <b>Usage:</b> If you would like to use this website template for your
      own leaderboard, please send Carlos & John an email requesting permission.
      If granted, please make sure to acknowledge the SWE-bench team and link to
      this leaderboard on the home page of the website.
    </p>
    <p class="text-content">
      Correspondence to: <a href="mailto:carlosej@princeton.edu">carlosej@princeton.edu</a>,
      <a href="mailto:johnby@stanford.edu">johnby@stanford.edu</a>
    </p>
    <div class="content-wrapper" style="display: flex; flex-direction: row; margin-top: 0.5em;">
      <a href="https://princeton-nlp.github.io/">
        <img src="img/princeton_seal.svg" style="height: 3em;padding-top:0.5em;padding-right: 1em" />
      </a>
      <a href="https://www.cs.stanford.edu/">
        <img src="img/stanford_logo.png" style="height: 3em;padding-top:0.5em;padding-right: 1em;padding-left: 0.25em;" />
      </a>
      <a href="https://pli.princeton.edu/">
        <img src="img/pli_logo.svg" style="height: 3em;padding-top:0.5em;padding-right: 1em" />
      </a>
      <a href="https://cs.uchicago.edu/">
        <img src="img/chicago_seal.svg" style="height: 3em;padding-top:0.5em;padding-right: 1em" />
      </a>
    </div>
  </div>
</div>

<script>
  document.addEventListener('DOMContentLoaded', function() {
    // Set Lite tab as default active tab
    document.getElementById('tab-lite').classList.add('active');
    document.getElementById('leaderboard-Lite').style.display = 'block';
    
    // Tab switching functionality
    const tabs = document.querySelectorAll('.tablinks');
    tabs.forEach(function(tab) {
      tab.addEventListener('click', function() {
        // Hide all tab content
        const tabContents = document.querySelectorAll('.tabcontent');
        tabContents.forEach(function(content) {
          content.style.display = 'none';
        });
        
        // Remove active class from all tabs
        tabs.forEach(function(t) {
          t.classList.remove('active');
        });
        
        // Show the clicked tab content and add active class to clicked tab
        const leaderboard = this.getAttribute('data-leaderboard');
        document.getElementById(`leaderboard-${leaderboard}`).style.display = 'block';
        this.classList.add('active');
      });
    });
  });
</script>
