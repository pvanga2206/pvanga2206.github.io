#!/usr/bin/env python3
"""
build.py — Reads content.md and generates index.html
Run: python3 build.py
"""

import re

def parse_content(text):
    data = {}
    lines = text.split('\n')

    # ── Header block (name + key/value pairs until first ---)
    header_lines = []
    i = 0
    data['name'] = lines[0].lstrip('# ').strip()
    i = 1
    while i < len(lines) and not lines[i].startswith('---'):
        header_lines.append(lines[i].strip())
        i += 1

    for line in header_lines:
        m = re.match(r'\*\*(.+?)\*\*:\s*(.+)', line)
        if m:
            data[m.group(1).lower()] = m.group(2).strip()

    # ── Split into ## sections
    sections = {}
    current = None
    current_lines = []
    for line in lines[i:]:
        if line.startswith('## '):
            if current:
                sections[current] = '\n'.join(current_lines).strip()
            current = line[3:].strip().lower()
            current_lines = []
        else:
            current_lines.append(line)
    if current:
        sections[current] = '\n'.join(current_lines).strip()

    # ── Hero stats
    stats = []
    for line in sections.get('hero stats', '').split('\n'):
        m = re.match(r'-\s*(.+?)\s*\*\*(.+?)\*\*\s*\|\s*(.+)', line)
        if m:
            stats.append({'icon': m.group(1).strip(), 'num': m.group(2).strip(), 'label': m.group(3).strip()})
    data['stats'] = stats

    # ── Skills
    skills_raw = sections.get('skills', '')
    data['skills'] = [s.strip() for s in skills_raw.split(',') if s.strip()]

    # ── Experience
    jobs = []
    for block in re.split(r'\n### ', sections.get('experience', '')):
        block = block.strip()
        if not block: continue
        job = {}
        block_lines = block.split('\n')
        job['title'] = block_lines[0].lstrip('# ').strip()
        job['bullets'] = []
        for bl in block_lines[1:]:
            m = re.match(r'\*\*(.+?)\*\*:\s*(.+)', bl.strip())
            if m:
                job[m.group(1).lower()] = m.group(2).strip()
            elif bl.strip().startswith('- '):
                job['bullets'].append(bl.strip()[2:])
        jobs.append(job)
    data['experience'] = jobs

    # ── Projects
    projects = []
    for block in re.split(r'\n### ', sections.get('projects', '')):
        block = block.strip()
        if not block: continue
        proj = {}
        block_lines = block.split('\n')
        proj['title'] = block_lines[0].lstrip('# ').strip()
        desc_lines = []
        for bl in block_lines[1:]:
            m = re.match(r'\*\*(.+?)\*\*:\s*(.+)', bl.strip())
            if m:
                key = m.group(1).lower()
                val = m.group(2).strip()
                if key == 'tags':
                    proj['tags'] = [t.strip() for t in val.split(',')]
                else:
                    proj[key] = val
            elif bl.strip():
                desc_lines.append(bl.strip())
        proj['desc'] = ' '.join(desc_lines)
        projects.append(proj)
    data['projects'] = projects

    # ── Education
    edu_list = []
    for block in re.split(r'\n### ', sections.get('education', '')):
        block = block.strip()
        if not block: continue
        edu = {}
        block_lines = block.split('\n')
        edu['degree'] = block_lines[0].lstrip('# ').strip()
        for bl in block_lines[1:]:
            m = re.match(r'\*\*(.+?)\*\*:\s*(.+)', bl.strip())
            if m:
                edu[m.group(1).lower()] = m.group(2).strip()
        edu_list.append(edu)
    data['education'] = edu_list

    # ── Certifications
    certs = []
    for line in sections.get('certifications', '').split('\n'):
        if line.strip().startswith('- '):
            certs.append(line.strip()[2:])
    data['certifications'] = certs

    # ── Publications
    pubs = []
    for line in sections.get('publications', '').split('\n'):
        if line.strip().startswith('- '):
            raw = line.strip()[2:]
            # parse **title** | [text](url) | desc
            parts = raw.split(' | ')
            pub = {}
            pub['title'] = re.sub(r'\*\*(.+?)\*\*', r'\1', parts[0]).strip()
            pub['desc'] = parts[2].strip() if len(parts) > 2 else ''
            link_m = re.search(r'\[(.+?)\]\((.+?)\)', parts[1]) if len(parts) > 1 else None
            if link_m:
                pub['link_text'] = link_m.group(1)
                pub['link_url'] = link_m.group(2)
            pubs.append(pub)
    data['publications'] = pubs

    return data


def render_html(d):
    # Stats cards
    stats_html = ''
    for s in d.get('stats', []):
        stats_html += f'''
      <div class="stat-card">
        <div class="stat-icon">{s["icon"]}</div>
        <div><div class="stat-num">{s["num"]}</div><div class="stat-label">{s["label"]}</div></div>
      </div>'''

    # Skills ticker (duplicated for seamless loop)
    ticker_items = ''
    for skill in d.get('skills', []):
        ticker_items += f'<span>{skill}</span><span>·</span>\n    '
    ticker_html = ticker_items * 2  # duplicate for loop

    # Experience timeline
    exp_html = ''
    for job in d.get('experience', []):
        bullets = ''.join(f'<li>{b}</li>' for b in job.get('bullets', []))
        exp_html += f'''
      <div class="tl-item">
        <div class="tl-date">
          <div class="tl-date-main">{job.get("period","")}</div>
          <div class="tl-date-loc">{job.get("location","")}</div>
        </div>
        <div class="tl-line-wrap"><div class="tl-dot"></div><div class="tl-vert"></div></div>
        <div class="tl-content">
          <div class="tl-role">{job.get("title","")}</div>
          <div class="tl-company">{job.get("company","")}</div>
          <ul class="tl-bullets">{bullets}</ul>
        </div>
      </div>'''

    # Projects
    proj_html = ''
    for proj in d.get('projects', []):
        tags = ''.join(f'<span class="tag">{t}</span>' for t in proj.get('tags', []))
        proj_html += f'''
      <div class="project-card">
        <div class="project-emoji">{proj.get("emoji","📁")}</div>
        <div class="project-title">{proj.get("title","")}</div>
        <p class="project-desc">{proj.get("desc","")}</p>
        <div class="project-metric">✦ {proj.get("metric","")}</div>
        <div class="project-tags">{tags}</div>
      </div>'''

    # Education
    edu_html = ''
    for edu in d.get('education', []):
        edu_html += f'''
      <div class="edu-card">
        <div class="edu-degree">{edu.get("degree","")}</div>
        <div class="edu-school">{edu.get("school","")}</div>
        <div class="edu-meta">{edu.get("year","")} · GPA {edu.get("gpa","")}</div>
      </div>'''

    # Certifications
    cert_html = ''.join(f'<li><span class="li-icon">✦</span><span>{c}</span></li>' for c in d.get('certifications', []))

    # Publications
    pub_html = ''
    for pub in d.get('publications', []):
        link = f'<a href="{pub["link_url"]}" target="_blank">{pub["link_text"]} →</a>' if pub.get('link_url') else ''
        pub_html += f'''<li><span class="li-icon">✦</span><span><strong>{pub["title"]}</strong><br>{pub.get("desc","")}<br>{link}</span></li>'''

    name = d.get('name', 'Portfolio')
    title = d.get('title', '')
    location = d.get('location', '')
    email = d.get('email', '')
    linkedin = d.get('linkedin', '')
    github = d.get('github', '')
    status = d.get('status', '')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{name} — {title}</title>
  <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --cream:#fdf8f3;--warm-white:#fff9f4;--terracotta:#c4673a;--terracotta-light:#e8846a;
      --rust:#a84e27;--warm-brown:#3d2b1f;--mid-brown:#6b4a35;--muted:#9c7b68;
      --border:#e8ddd4;--shadow:rgba(61,43,31,0.08);
    }}
    *{{margin:0;padding:0;box-sizing:border-box;}} html{{scroll-behavior:smooth;}}
    body{{font-family:'DM Sans',sans-serif;background:var(--cream);color:var(--warm-brown);line-height:1.7;}}
    nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;justify-content:space-between;align-items:center;padding:1.1rem 4rem;background:rgba(253,248,243,0.88);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);}}
    .nav-logo{{font-family:'Lora',serif;font-size:1.15rem;font-weight:600;color:var(--warm-brown);text-decoration:none;}}
    .nav-links{{display:flex;gap:2.5rem;list-style:none;}}
    .nav-links a{{text-decoration:none;font-size:0.875rem;font-weight:500;color:var(--mid-brown);letter-spacing:0.04em;text-transform:uppercase;transition:color 0.2s;}}
    .nav-links a:hover{{color:var(--terracotta);}}
    .hero{{min-height:100vh;display:flex;align-items:center;padding:8rem 4rem 4rem;position:relative;overflow:hidden;}}
    .hero::before{{content:'';position:absolute;top:-80px;right:-120px;width:600px;height:600px;background:radial-gradient(circle,rgba(196,103,58,0.12) 0%,transparent 70%);border-radius:50%;}}
    .hero-inner{{max-width:1100px;margin:0 auto;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:4rem;align-items:center;position:relative;z-index:1;}}
    .hero-tag{{display:inline-block;font-size:0.78rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--terracotta);background:rgba(196,103,58,0.1);padding:0.35rem 0.9rem;border-radius:100px;margin-bottom:1.2rem;animation:fadeUp 0.6s ease both;}}
    .hero h1{{font-family:'Lora',serif;font-size:clamp(2.8rem,4.5vw,4rem);font-weight:600;line-height:1.18;margin-bottom:1.2rem;animation:fadeUp 0.6s 0.1s ease both;}}
    .hero h1 em{{font-style:italic;color:var(--terracotta);}}
    .hero-desc{{font-size:1.05rem;color:var(--mid-brown);max-width:480px;margin-bottom:2rem;animation:fadeUp 0.6s 0.2s ease both;}}
    .hero-cta{{display:flex;gap:1rem;flex-wrap:wrap;animation:fadeUp 0.6s 0.3s ease both;}}
    .btn{{display:inline-flex;align-items:center;padding:0.75rem 1.8rem;border-radius:100px;font-size:0.9rem;font-weight:600;text-decoration:none;transition:all 0.2s ease;}}
    .btn-primary{{background:var(--terracotta);color:#fff;box-shadow:0 4px 18px rgba(196,103,58,0.3);}}
    .btn-primary:hover{{background:var(--rust);transform:translateY(-2px);}}
    .btn-outline{{background:transparent;color:var(--warm-brown);border:1.5px solid var(--border);}}
    .btn-outline:hover{{border-color:var(--terracotta);color:var(--terracotta);transform:translateY(-2px);}}
    .hero-right{{display:flex;flex-direction:column;gap:1rem;animation:fadeUp 0.6s 0.4s ease both;}}
    .stat-card{{background:var(--warm-white);border:1px solid var(--border);border-radius:16px;padding:1.4rem 1.6rem;display:flex;align-items:center;gap:1.2rem;box-shadow:0 2px 16px var(--shadow);transition:transform 0.2s,box-shadow 0.2s;}}
    .stat-card:hover{{transform:translateY(-3px);box-shadow:0 8px 28px var(--shadow);}}
    .stat-icon{{width:48px;height:48px;background:rgba(196,103,58,0.1);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;}}
    .stat-num{{font-family:'Lora',serif;font-size:1.6rem;font-weight:600;line-height:1;}}
    .stat-label{{font-size:0.82rem;color:var(--muted);margin-top:0.15rem;}}
    .skills-strip{{background:var(--warm-brown);padding:1.5rem 4rem;overflow:hidden;}}
    .skills-ticker{{display:flex;gap:3rem;animation:ticker 25s linear infinite;white-space:nowrap;}}
    .skills-ticker span{{font-size:0.82rem;font-weight:500;letter-spacing:0.06em;text-transform:uppercase;color:rgba(253,248,243,0.7);flex-shrink:0;}}
    @keyframes ticker{{0%{{transform:translateX(0);}}100%{{transform:translateX(-50%);}}}}
    section{{padding:6rem 4rem;}}
    .section-inner{{max-width:1100px;margin:0 auto;}}
    .section-label{{font-size:0.78rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--terracotta);margin-bottom:0.6rem;}}
    .section-title{{font-family:'Lora',serif;font-size:clamp(1.8rem,3vw,2.4rem);font-weight:600;margin-bottom:3rem;}}
    #experience{{background:var(--warm-white);}}
    .timeline{{display:flex;flex-direction:column;}}
    .tl-item{{display:grid;grid-template-columns:180px 1px 1fr;gap:0 2rem;padding-bottom:3rem;opacity:0;transform:translateY(24px);transition:opacity 0.5s ease,transform 0.5s ease;}}
    .tl-item.visible{{opacity:1;transform:translateY(0);}}
    .tl-date{{text-align:right;padding-top:0.2rem;}}
    .tl-date-main{{font-size:0.82rem;font-weight:600;color:var(--terracotta);text-transform:uppercase;letter-spacing:0.04em;}}
    .tl-date-loc{{font-size:0.78rem;color:var(--muted);margin-top:0.2rem;}}
    .tl-line-wrap{{display:flex;flex-direction:column;align-items:center;}}
    .tl-dot{{width:12px;height:12px;background:var(--terracotta);border-radius:50%;border:3px solid var(--cream);box-shadow:0 0 0 2px var(--terracotta);flex-shrink:0;margin-top:0.25rem;}}
    .tl-vert{{flex:1;width:1px;background:var(--border);}}
    .tl-role{{font-family:'Lora',serif;font-size:1.15rem;font-weight:600;}}
    .tl-company{{font-size:0.88rem;color:var(--muted);margin-bottom:0.8rem;}}
    .tl-bullets{{list-style:none;}}
    .tl-bullets li{{font-size:0.92rem;color:var(--mid-brown);padding:0.25rem 0 0.25rem 1.1rem;position:relative;}}
    .tl-bullets li::before{{content:'→';position:absolute;left:0;color:var(--terracotta-light);font-size:0.75rem;top:0.35rem;}}
    .projects-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1.8rem;}}
    .project-card{{background:var(--warm-white);border:1px solid var(--border);border-radius:20px;padding:2rem;opacity:0;transform:translateY(24px);transition:opacity 0.5s ease,transform 0.5s ease,box-shadow 0.2s;position:relative;overflow:hidden;}}
    .project-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--terracotta),var(--terracotta-light));opacity:0;transition:opacity 0.2s;}}
    .project-card:hover::before{{opacity:1;}}
    .project-card.visible{{opacity:1;transform:translateY(0);}}
    .project-card:hover{{transform:translateY(-4px);box-shadow:0 12px 40px var(--shadow);}}
    .project-emoji{{font-size:2rem;margin-bottom:1rem;}}
    .project-title{{font-family:'Lora',serif;font-size:1.15rem;font-weight:600;margin-bottom:0.6rem;}}
    .project-desc{{font-size:0.9rem;color:var(--mid-brown);line-height:1.65;margin-bottom:1.2rem;}}
    .project-tags{{display:flex;flex-wrap:wrap;gap:0.4rem;}}
    .tag{{font-size:0.75rem;font-weight:500;color:var(--terracotta);background:rgba(196,103,58,0.1);padding:0.25rem 0.7rem;border-radius:100px;}}
    .project-metric{{display:inline-flex;align-items:center;font-size:0.82rem;font-weight:600;color:var(--terracotta);margin-top:0.8rem;}}
    #extras{{background:var(--warm-white);}}
    .extras-grid{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;}}
    .extras-card{{background:var(--cream);border:1px solid var(--border);border-radius:16px;padding:1.8rem;}}
    .extras-card h3{{font-family:'Lora',serif;font-size:1rem;font-weight:600;margin-bottom:1.2rem;}}
    .extras-list{{list-style:none;}}
    .extras-list li{{font-size:0.88rem;color:var(--mid-brown);padding:0.5rem 0;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;gap:0.6rem;}}
    .extras-list li:last-child{{border-bottom:none;}}
    .li-icon{{color:var(--terracotta);flex-shrink:0;}}
    .extras-list a{{color:var(--terracotta);text-decoration:none;}}
    .extras-list a:hover{{text-decoration:underline;}}
    .edu-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:2rem;}}
    .edu-card{{background:var(--cream);border:1px solid var(--border);border-radius:16px;padding:1.6rem;}}
    .edu-degree{{font-family:'Lora',serif;font-size:1rem;font-weight:600;margin-bottom:0.3rem;}}
    .edu-school{{font-size:0.88rem;color:var(--muted);}}
    .edu-meta{{font-size:0.82rem;color:var(--terracotta);font-weight:600;margin-top:0.5rem;}}
    #contact{{background:var(--warm-brown);text-align:center;}}
    #contact .section-label{{color:var(--terracotta-light);}}
    #contact .section-title{{color:var(--cream);margin-bottom:1rem;}}
    #contact p{{color:rgba(253,248,243,0.65);margin-bottom:2.5rem;}}
    .contact-links{{display:flex;justify-content:center;gap:1.2rem;flex-wrap:wrap;}}
    .contact-link{{display:inline-flex;align-items:center;gap:0.6rem;padding:0.75rem 1.6rem;border-radius:100px;font-size:0.9rem;font-weight:600;text-decoration:none;transition:all 0.2s;}}
    .contact-link-primary{{background:var(--terracotta);color:#fff;}}
    .contact-link-primary:hover{{background:var(--terracotta-light);transform:translateY(-2px);}}
    .contact-link-ghost{{border:1.5px solid rgba(253,248,243,0.25);color:var(--cream);}}
    .contact-link-ghost:hover{{border-color:var(--terracotta-light);color:var(--terracotta-light);transform:translateY(-2px);}}
    footer{{background:var(--warm-brown);border-top:1px solid rgba(255,255,255,0.08);text-align:center;padding:1.5rem;font-size:0.78rem;color:rgba(253,248,243,0.35);}}
    @keyframes fadeUp{{from{{opacity:0;transform:translateY(20px);}}to{{opacity:1;transform:translateY(0);}}}}
    @media(max-width:768px){{
      nav{{padding:1rem 1.5rem;}} .nav-links{{display:none;}}
      .hero,section{{padding:5rem 1.5rem 3rem;}}
      .hero-inner{{grid-template-columns:1fr;gap:2.5rem;}}
      .tl-item{{grid-template-columns:1fr;gap:0.5rem;}}
      .tl-date{{text-align:left;}} .tl-line-wrap{{display:none;}}
      .extras-grid,.edu-grid{{grid-template-columns:1fr;}}
    }}
  </style>
</head>
<body>

<nav>
  <a class="nav-logo" href="#">{name}</a>
  <ul class="nav-links">
    <li><a href="#experience">Experience</a></li>
    <li><a href="#projects">Projects</a></li>
    <li><a href="#extras">More</a></li>
    <li><a href="#contact">Contact</a></li>
  </ul>
</nav>

<section class="hero" id="home">
  <div class="hero-inner">
    <div>
      <div class="hero-tag">{status}</div>
      <h1>Hi, I\'m {name.split()[0]} —<br>a <em>{title}</em></h1>
      <p class="hero-desc">I turn messy, complex data into clean pipelines and clear insights. Based in {location}, specialising in Azure, SQL, Python, and BI tools.</p>
      <div class="hero-cta">
        <a href="#experience" class="btn btn-primary">See My Work</a>
        <a href="mailto:{email}" class="btn btn-outline">Get in Touch</a>
      </div>
    </div>
    <div class="hero-right">{stats_html}</div>
  </div>
</section>

<div class="skills-strip">
  <div class="skills-ticker">{ticker_html}</div>
</div>

<section id="experience">
  <div class="section-inner">
    <div class="section-label">Career</div>
    <div class="section-title">Work Experience</div>
    <div class="timeline">{exp_html}</div>
  </div>
</section>

<section id="projects">
  <div class="section-inner">
    <div class="section-label">Work</div>
    <div class="section-title">Featured Projects</div>
    <div class="projects-grid">{proj_html}</div>
  </div>
</section>

<section id="extras">
  <div class="section-inner">
    <div class="section-label">Background</div>
    <div class="section-title">Education & More</div>
    <div class="edu-grid">{edu_html}</div>
    <div class="extras-grid">
      <div class="extras-card">
        <h3>🏅 Certifications</h3>
        <ul class="extras-list">{cert_html}</ul>
      </div>
      <div class="extras-card">
        <h3>📚 Publications</h3>
        <ul class="extras-list">{pub_html}</ul>
      </div>
    </div>
  </div>
</section>

<section id="contact">
  <div class="section-inner">
    <div class="section-label">Let\'s Talk</div>
    <div class="section-title">Get in Touch</div>
    <p>Open to data engineering and analytics roles. I\'d love to hear from you.</p>
    <div class="contact-links">
      <a href="mailto:{email}" class="contact-link contact-link-primary">✉ {email}</a>
      <a href="{linkedin}" target="_blank" class="contact-link contact-link-ghost">LinkedIn</a>
      <a href="{github}" target="_blank" class="contact-link contact-link-ghost">GitHub</a>
    </div>
  </div>
</section>

<footer>© 2026 {name} — Built with care</footer>

<script>
  const observer = new IntersectionObserver((entries) => {{
    entries.forEach((e, i) => {{
      if (e.isIntersecting) setTimeout(() => e.target.classList.add('visible'), i * 80);
    }});
  }}, {{ threshold: 0.12 }});
  document.querySelectorAll('.tl-item, .project-card').forEach(el => observer.observe(el));
</script>
</body>
</html>'''


if __name__ == '__main__':
    import sys, os
    md_path = 'content.md'
    out_path = 'index.html'

    if not os.path.exists(md_path):
        print(f"❌ Could not find {md_path}")
        sys.exit(1)

    with open(md_path, 'r') as f:
        text = f.read()

    data = parse_content(text)
    html = render_html(data)

    with open(out_path, 'w') as f:
        f.write(html)

    print(f"✅ Built {out_path} successfully!")
