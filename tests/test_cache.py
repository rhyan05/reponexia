from reponexia.cache import Cache, cache_key


def test_chave_muda_com_cada_campo():
    assert cache_key("a", "b") == cache_key("a", "b")
    assert cache_key("a", "b") != cache_key("a", "c")
    # separador evita colisão "ab"+"c" vs "a"+"bc"
    assert cache_key("ab", "c") != cache_key("a", "bc")


def test_roundtrip_get_set_save(tmp_path):
    path = tmp_path / ".reponexia" / "cache.json"

    cache = Cache(path)
    assert cache.get("k") is None
    cache.set("k", "resumo")
    cache.save()

    assert Cache(path).get("k") == "resumo"


def test_arquivo_corrompido_vira_cache_vazio(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("{nao é json", encoding="utf-8")

    assert Cache(path).get("k") is None
