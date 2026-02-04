import os
import re

# Define the navigation items
# Name, Icon, Folder
NAV_ITEMS = [
    ("Nexus Hub", "hub", ""), # index.html is in the parent
    ("Mission Control", "dashboard", "craft_mission_control_dashboard"),
    ("Workflow Builder", "account_tree", "craft_workflow_builder"),
    ("Agent Fleet", "smart_toy", "craft_agent_fleet_management"),
    ("Knowledge Base", "database", "craft_knowledge_base_rag"),
    ("Live Execution", "play_circle", "craft_live_workflow_execution"),
    ("Health Monitor", "monitoring", "craft_system_health_monitor"),
    ("Settings & API", "settings", "craft_global_settings_&_api"),
    ("Thought Log", "psychology", "craft_agent_thought_log"),
    ("Task History", "history", "craft_task_history_&_archive"),
]

STITCH_DIR = "/Users/stefano/Documents/Progetti_personali/CRAFT/stitch"

def generate_sidebar_html(current_folder):
    html = '            <!-- Unified Nav -->\n            <nav class="flex flex-col p-3 gap-1 overflow-y-auto flex-1">\n'
    
    for name, icon, folder in NAV_ITEMS:
        is_active = folder == current_folder
        
        # Link logic
        if folder == "":
            href = "../index.html"
        else:
            href = f"../{folder}/code.html"
            
        if is_active:
            classes = "flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10 text-primary"
            icon_classes = "material-symbols-outlined text-[20px] fill-1"
        else:
            classes = "flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            icon_classes = "material-symbols-outlined text-[20px]"
            
        html += f'                <a class="{classes}" href="{href}">\n'
        html += f'                    <span class="{icon_classes}">{icon}</span>\n'
        html += f'                    <span class="text-sm font-medium">{name}</span>\n'
        if is_active:
            html += '                    <div class="ml-auto size-1.5 rounded-full bg-primary shadow-[0_0_8px_#0da6f2]"></div>\n'
        html += '                </a>\n'
        
    html += '            </nav>'
    return html

def process_file(filepath, folder):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # 1. Update branding to be a link to index
    content = re.sub(
        r'<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">\s*<span class="material-symbols-outlined text-primary">hub</span>\s*CRAFT\s*</h1>',
        r'<a href="../index.html" class="hover:opacity-80 transition-opacity"><h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2"><span class="material-symbols-outlined text-primary">hub</span>CRAFT</h1></a>',
        content
    )
    
    # Also handle the variant from Mission Control
    content = re.sub(
        r'<div class="flex items-center gap-3 mb-10">.*?</div>\s*</div>',
        lambda m: f'<a href="../index.html" class="flex items-center gap-3 mb-10 hover:opacity-80 transition-opacity"><div class="size-8 rounded bg-primary/20 flex items-center justify-center border border-primary/40 text-primary"><span class="material-symbols-outlined text-xl">hub</span></div><div><h1 class="text-white text-lg font-bold tracking-wider leading-none">CRAFT</h1><p class="text-xs text-slate-500 font-mono mt-0.5">{folder.replace("_", " ").upper()}</p></div></a>',
        content,
        flags=re.DOTALL
    )

    # 2. Replace the <nav> block
    # We look for <nav class="...">...</nav>
    new_nav = generate_sidebar_html(folder)
    content = re.sub(r'<nav class="flex flex-col p-3 gap-1">.*?</nav>', new_nav, content, flags=re.DOTALL)
    content = re.sub(r'<nav class="flex flex-col gap-2">.*?</nav>', new_nav, content, flags=re.DOTALL)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✅ Processed {filepath}")

for _, _, folder in NAV_ITEMS:
    if folder == "": continue
    path = os.path.join(STITCH_DIR, folder, "code.html")
    if os.path.exists(path):
        process_file(path, folder)
    else:
        print(f"⚠️ Skip {path} (not found)")
