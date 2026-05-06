from tritium_bridge.config import load
from tritium_bridge.personas import system_prompt_for
from tritium_bridge.worldcontext import build_recent_world

cfg = load()
agent = 'Bridge'
world = build_recent_world(cfg, agent)
sp = system_prompt_for(cfg, agent, world_context=world)
print('===== ASSEMBLED SYSTEM PROMPT (Bridge) =====')
print(sp)
print('===== END =====')
print()
print(f'TOTAL_CHARS={len(sp)}  APPROX_TOKENS={len(sp)//4}')
print('CONTAINS_SOL=' + str('Sol' in sp))
print('CONTAINS_SOLOMON=' + str('Solomon' in sp))
print('BISHOP_NOTED=' + str('Bishop' in sp))
print('WORLD_SECTION_PRESENT=' + str(bool(world)))
