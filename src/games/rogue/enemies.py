

def diagMethod():
    pass
    
item1 = {
    'name': 'diagnostic lens',
    'desc': 'this lens grants insight',
    'type': 'active',
    'moveset': [
        {
            'name': 'analyze',
            'targets': 1,
            'method': diagMethod,
        }
    ]
    'stat bonus': {}
}

enemyTemplate = {
    'name': 'sentry bot',
    'x': 0,
    'y':0,
    'hp': 10.0,
    'inventory': [
        {
            'name': 'diagnostic lens',
            'desc': 'this lens grants insight',
            'type': 'active',
        },
        {
            'name': 'stun module',
        },
    ]
    #'attacks' these should come from inv items
    #'armor' this as well
    'stats': { #base stats
        'strength': 0,
        'tech': 5,
        'speed': 0.5, # units / sec
        'heat resistance': 5,
        'physical resistance': 2,
        'electrical resistance': 1,
        'radiation resistance': 3,
    }
}
