
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update DCF Bar Colors: Green (Cheap) -> Blue (Target) -> Red (Expensive)
    # Current: Danger(Red) -> Success(Green) -> Primary(Blue)
    # Change to: Success(Green/Buy) -> Primary(Blue/Fair) -> Danger(Red/Risk)
    old_colors = """<div class="h-full bg-brand-danger/40 w-1/3 border-r border-black/20"></div>
                                                <div class="h-full bg-brand-success/40 w-1/3 border-r border-black/20"></div>
                                                <div class="h-full bg-brand-primary/40 w-1/3"></div>"""
    
    new_colors = """<div class="h-full bg-brand-success/40 w-1/3 border-r border-black/20"></div>
                                                <div class="h-full bg-brand-primary/40 w-1/3 border-r border-black/20"></div>
                                                <div class="h-full bg-brand-danger/40 w-1/3"></div>"""
    
    content = content.replace(old_colors.strip(), new_colors.strip())

    # 2. Implement Dynamic Upside Calculation in loadSymbol function
    # Find where 'ai-upside': `${data.upside} 상승 여력` is set and replace with dynamic logic
    
    dynamic_upside_logic = """
            // Dynamic Upside Calculation
            const targetPrice = parseFloat(data.dcf_target.toString().replace('$', ''));
            const currentPrice = parseFloat(data.price);
            if (!isNaN(targetPrice) && !isNaN(currentPrice) && currentPrice > 0) {
                const calculatedUpside = ((targetPrice - currentPrice) / currentPrice * 100).toFixed(1);
                const upsideEl = document.getElementById('ai-upside');
                if (upsideEl) {
                    upsideEl.innerText = `${calculatedUpside > 0 ? '+' : ''}${calculatedUpside}% 예상 상승 여력`;
                    upsideEl.className = `mt-4 text-xs font-bold ${calculatedUpside > 0 ? 'text-brand-success' : 'text-brand-danger'} uppercase tracking-widest`;
                }
            } else {
                document.getElementById('ai-upside').innerText = `${data.upside} 상승 여력`;
            }
    """

    # We need to insert this before or after the loop that sets fields
    # Let's target the fields loop
    old_fields_setting = """            for (const [id, val] of Object.entries(fields)) {
                const el = document.getElementById(id);
                if (el) el.innerText = val || '--';
            }"""
    
    insertion_point = old_fields_setting + dynamic_upside_logic
    content = content.replace(old_fields_setting, insertion_point)

    # 3. Adjust the DCF Target labels color to match the Blue/Primary middle zone
    content = content.replace('text-brand-primary mb-1">TARGET', 'text-brand-primary mb-1">FAIR VALUE')
    content = content.replace('text-brand-primary font-black text-sm">--', 'text-brand-primary font-black text-sm">--') # Already okay

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("SUCCESS: DCF colors and dynamic upside logic updated.")

except Exception as e:
    print(f"ERROR: {e}")
