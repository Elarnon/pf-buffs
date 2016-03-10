from django.db.models import F

def build_stats(qs):
    grid = qs.filter(bonus__isnull=False).annotate(
        stacks=F("bonus__typ__stacks"),
        source=F("name_fr"),
        typ=F("bonus__typ__name_fr"),
        typ_id=F("bonus__typ_id"),
        constraint=F("bonus__constraint__name_fr"),
        constraint_id=F("bonus__constraint_id"),
        value=F("bonus__value"),
        stat=F("bonus__stat__name_fr"),
        stat_id=F("bonus__stat_id"),
    ).values(
            "pk", "source", "stat", "stat_id", "constraint", "constraint_id", "value", "typ", "typ_id", "stacks")

    sources = {}
    for elt in grid:
        source_id = elt['pk']
        assert(source_id is not None)
        if source_id not in sources:
            sources[source_id] = { 'name': elt['source'], 'stats': { } }
        source = sources[source_id]

        stat_id = elt['stat_id']
        if stat_id is None:
            print(elt)
        assert(stat_id is not None)
        if stat_id not in source['stats']:
            source['stats'][stat_id] = { 'name': elt['stat'], 'constraints': { } }
        stat = source['stats'][stat_id]

        constraint_id = elt['constraint_id']
        if constraint_id not in stat['constraints']:
            stat['constraints'][constraint_id] = { 'name': elt['constraint'], 'typs': { } }
        constraint = stat['constraints'][constraint_id]

        typ_id = elt['typ_id']
        if typ_id is not None:
            assert(elt['value'] > 0)

        assert(typ_id not in constraint['typs'])
        constraint['typs'][typ_id] = { 'name': elt['typ'], 'stacks': elt['stacks'], 'value': elt['value'] }

    return sources

def filter_typs(stats, fn):
    for stat in stats:
        todelete = set()
        for cid, constraint in stat['constraints'].items():
            constraint['typs'] = { tid: typ for tid, typ in constraint['typs'].items() if fn(typ) }
            if not constraint['typs']:
                todelete.add(cid)
        for cid in todelete:
            del stat['constraints'][cid]
    return [stat for stat in stats if stat['constraints']]

def compute_constrained(stats):
    for stat in stats:
        if None not in stat['constraints']:
            continue

        baseline = stat['constraints'][None]
        
        emptyconstraints = set()
        for cid, constraint in stat['constraints'].items():
            if constraint['name'] is None:
                continue

            todelete = set()
            for tid, typ in constraint['typs'].items():
                if tid not in baseline['typs']:
                    continue
                base = baseline['typs'][tid]
                typ['value'] -= base['value']
                if typ['value'] <= 0:
                    todelete.add(tid)
            for tid in todelete:
                del constraint['typs'][tid]
            if not constraint['typs']:
                emptyconstraints.add(cid)
        for cid in emptyconstraints:
            del stat['constraints'][cid]
    return [stat for stat in stats if stat['constraints']]

def combine_sources(sources):
    combined_stats = {}
    for source in sources:
        for sid, stat in source['stats'].items():
            if sid not in combined_stats:
                combined_stats[sid] = { 'name': stat['name'], 'constraints': { } }
            combined_stat = combined_stats[sid]

            for cid, constraint in stat['constraints'].items():
                if cid not in combined_stat['constraints']:
                    combined_stat['constraints'][cid] = { 'name': constraint['name'], 'typs': { } }
                combined_constraint = combined_stat['constraints'][cid]

                for tid, typ in constraint['typs'].items():
                    if tid not in combined_constraint['typs']:
                        combined_constraint['typs'][tid] = { 'name': typ['name'], 'value': 0 }
                    combined_typ = combined_constraint['typs'][tid]

                    if tid is None or typ['stacks']:
                        combined_typ['value'] += typ['value']
                    else:
                        combined_typ['value'] = max(combined_typ['value'], typ['value'])


    for stat in combined_stats.values():
        todelete = set()
        for cid, constraint in stat['constraints'].items():
            constraint['typs'] = { tid: typ for tid, typ in constraint['typs'].items() if typ['value'] != 0 }
            if not constraint['typs']:
                todelete.add(cid)
        for cid in todelete:
            del stat['constraints'][cid]

    return [stat for stat in combined_stats.values() if stat['constraints']]

def cleanup(stats):
    return [
        stat for stat in stats
        if stat['value'] != 0 or max(constraint['value'] for constraint in stat['constraints']) > 0
    ]

def format_stats(stats):
    return [
        {
            'name': stat['name'],
            'value': sum(typ['value'] for typ in stat['constraints'][None]['typs'].values()) if None in stat['constraints'] else 0,
            'detail': sorted(stat['constraints'][None]['typs'].values(), key=lambda x: x['name'] or '') if None in stat['constraints'] else [],
            'constraints': sorted([
                {
                    'name': constraint['name'],
                    'value': sum(typ['value'] for typ in constraint['typs'].values()),
                    'detail': sorted(constraint['typs'].values(), key=lambda x: x['name'] or '')
                }
                for constraint in stat['constraints'].values()
                if constraint['name'] is not None
            ], key=lambda x: x['name'] or '')
        }
        for stat in stats
    ]

def make_stats(sources, fn=None, pr=False):
    stats = combine_sources(sources)
    if fn is not None:
        stats = filter_typs(stats, fn)
    stats = compute_constrained(stats)
    if pr:
        print(stats)
    return format_stats(stats)
