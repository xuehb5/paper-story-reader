"""Explicit study-type routing. A valid route is not evidence of scientific correctness."""
STUDY_TYPES = {
    'experimental': 'Experiment, controls, observations and bounded interpretation',
    'computational': 'Task/model, method, evaluation protocol and results',
    'observational': 'Sampling, measurement, associations and alternative explanations',
    'theoretical': 'Definitions, assumptions, derivation/proof and scope',
    'evidence_synthesis': 'Question, retrieval/selection, synthesis and uncertainty',
    'interpretive': 'Question, concepts/materials, interpretation and alternatives',
}
EDGE_TYPES = {'support', 'comparison', 'interpretation', 'deduction', 'assumption',
              'contradiction', 'association', 'next_question', 'limitation', 'evidence'}


def resolve(case):
    raw = case.get('reading_profile')
    if raw is None:
        return {'study_types': ['experimental'], 'disciplines': ['materials_chemistry'],
                'rationale': 'Legacy v0.21 input: retain original experimental/materials checks.',
                'legacy': True}
    if not isinstance(raw, dict):
        raise ValueError('reading_profile must be an object')
    types, disciplines = raw.get('study_types'), raw.get('disciplines')
    if (not isinstance(types, list) or not types or len(types) != len(set(types))
            or any(t not in STUDY_TYPES for t in types)):
        raise ValueError('reading_profile needs unique supported study_types; first is the primary route')
    if (not isinstance(disciplines, list) or not disciplines
            or any(not isinstance(x, str) or not x.strip() for x in disciplines)):
        raise ValueError('reading_profile needs actual disciplines')
    if not isinstance(raw.get('rationale'), str) or len(raw['rationale'].strip()) < 20:
        raise ValueError('reading_profile needs a source-informed routing rationale')
    return {**raw, 'legacy': False}


def validate_materials(case, sources):
    """Status describes availability, never proof that every source has been read."""
    records = case.get('materials')
    if records is None:
        return []  # Original reviewed inputs remain byte-for-byte usable.
    if not isinstance(records, list):
        return ['case.materials must be a list']
    errors, roles = [], set()
    allowed = {'main', 'supplement', 'appendix', 'extended_data', 'code', 'data', 'other'}
    states = {'available', 'not_provided', 'not_published', 'not_applicable'}
    seen = set()
    for item in records:
        if not isinstance(item, dict):
            errors.append('material inventory entry must be an object'); continue
        ident = item.get('id')
        if not ident or ident in seen:
            errors.append('material inventory needs unique ids')
        seen.add(ident)
        role, state = item.get('role'), item.get('status')
        roles.add(role)
        if role not in allowed or state not in states:
            errors.append('unknown material role/status')
        if not item.get('note'):
            errors.append('material inventory needs a truthful availability/reading note')
        sid = item.get('source')
        if state == 'available' and sid not in sources:
            errors.append('available material must identify a local, hash-checked source')
        if state != 'available' and sid:
            errors.append('unavailable material cannot identify an available source')
        if state in {'not_published', 'not_applicable'} and not item.get('basis'):
            errors.append('absence/not-applicability needs an actual source basis')
    if 'main' not in roles:
        errors.append('material inventory needs the main paper')
    return errors
