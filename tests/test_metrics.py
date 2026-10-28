def test_metrics_counts_requests(client):
    client.get("/health")
    text = client.get("/metrics").text
    assert 'http_requests_total{method="GET",path="/health",status="200"}' in text

def test_metrics_uses_route_template_not_raw_path(client):
    client.get("/encounters/some-boss/report", params={"run_id": "x"})
    text = client.get("/metrics").text
    assert 'path="/encounters/{encounter}/report"' in text
    assert "some-boss" not in text