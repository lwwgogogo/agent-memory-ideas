"""Data-format conversion only: no ordering, candidate balancing or score aggregation."""
class Item:
    def __init__(self,ident,memory,metadata):
        self.id=ident;self.memory=memory;self.metadata=metadata
class TextMemory:
    def __init__(self):self.items={}
    def get(self,ident):return self.items[ident]
    def update(self,ident,payload):
        self.items[ident]=Item(ident,payload['memory'],payload['metadata'])
class Cube:
    def __init__(self):self.text_mem=TextMemory()
class StorageBoundary:
    def __init__(self):self.mem_cubes={'audit':Cube()}
def episodes(rows):
    return [{'episode_id':r['id'],'final_score':r['outcome'],'success':bool(r['outcome']),
             'steps':[{'state':r['state'],'action':r['action'],'reward':r['outcome']}]} for r in rows]
def storage(rows):
    mos=StorageBoundary();bank=mos.mem_cubes['audit'].text_mem
    for r in rows:
        bank.items[r['id']]=Item(r['id'],f"state={r['state']} action={r['action']} outcome={r['outcome']}",
                                 {'state':r['state'],'action':r['action']})
    return mos
def candidates(rows,mos):
    bank=mos.mem_cubes['audit'].text_mem
    return [{'memory_id':r['id'],'action':r['action'],'state':r['state'],
             'metadata':dict(bank.items[r['id']].metadata),'similarity':0.5} for r in rows]
