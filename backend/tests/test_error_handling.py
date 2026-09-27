from app import create_app


def test_unhandled_exception_returns_generic_error_outside_debug():
    app = create_app("production")

    @app.route("/__boom")
    def boom():
        raise RuntimeError("a secret detail that must not leak")

    client = app.test_client()
    response = client.get("/__boom")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert "secret detail" not in response.get_data(as_text=True)


def test_unknown_route_still_returns_a_normal_404(client):
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
