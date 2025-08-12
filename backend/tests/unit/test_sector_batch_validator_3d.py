from services.sector_batch_validator_3d import get_batch_validator_3d, SectorBatchValidationError3D


def test_validator_3d_completeness_pass():
    v = get_batch_validator_3d()
    sectors = {
        "basic_materials": {"sentiment_score": 0.0},
        "communication_services": {"sentiment_score": 0.0},
        "consumer_cyclical": {"sentiment_score": 0.0},
        "consumer_defensive": {"sentiment_score": 0.0},
        "energy": {"sentiment_score": 0.0},
        "financial_services": {"sentiment_score": 0.0},
        "healthcare": {"sentiment_score": 0.0},
        "industrials": {"sentiment_score": 0.0},
        "real_estate": {"sentiment_score": 0.0},
        "technology": {"sentiment_score": 0.0},
        "utilities": {"sentiment_score": 0.0},
    }
    batch = v.prepare_batch(sectors)
    assert len(batch) == 11


def test_validator_3d_completeness_fail():
    v = get_batch_validator_3d()
    sectors = {
        "technology": {"sentiment_score": 0.0},
    }
    try:
        v.prepare_batch(sectors)
        assert False, "expected failure"
    except SectorBatchValidationError3D:
        assert True


