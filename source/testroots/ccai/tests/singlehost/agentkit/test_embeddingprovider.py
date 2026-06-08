"""
    .. module:: ccai.tests.singlehost.agentkit.test_embeddingprovider
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the EmbeddingProvider abstract base class.
"""

from ccai.agentkit.embeddingprovider import EmbeddingProvider
from ccai.agentkit.errors import SemanticError


# ---- Concrete Test Subclass ----


class StubEmbeddingProvider(EmbeddingProvider):
    """
        Minimal concrete subclass of EmbeddingProvider for testing
        the base class behavior.
    """

    def embed(self, text: str) -> list:
        if text is None or len(text.strip()) == 0:
            errmsg = "Cannot embed empty text."
            raise SemanticError(errmsg)
        rtnval = [0.0] * self.embedding_dimension
        return rtnval

    def embed_batch(self, texts: list) -> list:
        rtnval = [self.embed(text=t) for t in texts]
        return rtnval


# ---- Construction Tests ----


def test_embeddingprovider_construction_valid():
    """
        Verify that a valid EmbeddingProvider can be constructed.
    """
    provider = StubEmbeddingProvider(
        provider_name="test-provider",
        embedding_dimension=128,
    )

    assert provider.provider_name == "test-provider", "provider_name should match"
    assert provider.embedding_dimension == 128, "embedding_dimension should match"
    return


def test_embeddingprovider_construction_with_credentials():
    """
        Verify that credential_names are stored correctly.
    """
    provider = StubEmbeddingProvider(
        provider_name="test-provider",
        embedding_dimension=64,
        credential_names=["api-key", "secret"],
    )

    creds = provider.credential_names
    assert len(creds) == 2, "should have 2 credential names"
    assert "api-key" in creds, "should contain 'api-key'"
    assert "secret" in creds, "should contain 'secret'"
    return


def test_embeddingprovider_construction_default_credentials():
    """
        Verify that credential_names defaults to an empty list.
    """
    provider = StubEmbeddingProvider(
        provider_name="test-provider",
        embedding_dimension=64,
    )

    creds = provider.credential_names
    assert len(creds) == 0, "default credential_names should be empty"
    return


def test_embeddingprovider_credential_names_defensive_copy():
    """
        Verify that credential_names returns a defensive copy.
    """
    provider = StubEmbeddingProvider(
        provider_name="test-provider",
        embedding_dimension=64,
        credential_names=["api-key"],
    )

    creds = provider.credential_names
    creds.append("injected")

    assert len(provider.credential_names) == 1, "modifying returned list should not affect provider"
    return


# ---- Construction Validation Tests ----


def test_embeddingprovider_empty_name_raises_semantic_error():
    """
        Verify that constructing with an empty provider_name raises SemanticError.
    """
    raised = False
    try:
        StubEmbeddingProvider(provider_name="", embedding_dimension=128)
    except SemanticError:
        raised = True

    assert raised is True, "empty provider_name should raise SemanticError"
    return


def test_embeddingprovider_none_name_raises_semantic_error():
    """
        Verify that constructing with None provider_name raises SemanticError.
    """
    raised = False
    try:
        StubEmbeddingProvider(provider_name=None, embedding_dimension=128)
    except SemanticError:
        raised = True

    assert raised is True, "None provider_name should raise SemanticError"
    return


def test_embeddingprovider_whitespace_name_raises_semantic_error():
    """
        Verify that constructing with whitespace-only provider_name raises SemanticError.
    """
    raised = False
    try:
        StubEmbeddingProvider(provider_name="   ", embedding_dimension=128)
    except SemanticError:
        raised = True

    assert raised is True, "whitespace-only provider_name should raise SemanticError"
    return


def test_embeddingprovider_zero_dimension_raises_semantic_error():
    """
        Verify that constructing with embedding_dimension=0 raises SemanticError.
    """
    raised = False
    try:
        StubEmbeddingProvider(provider_name="test", embedding_dimension=0)
    except SemanticError:
        raised = True

    assert raised is True, "embedding_dimension=0 should raise SemanticError"
    return


def test_embeddingprovider_negative_dimension_raises_semantic_error():
    """
        Verify that constructing with a negative embedding_dimension raises SemanticError.
    """
    raised = False
    try:
        StubEmbeddingProvider(provider_name="test", embedding_dimension=-5)
    except SemanticError:
        raised = True

    assert raised is True, "negative embedding_dimension should raise SemanticError"
    return


def test_embeddingprovider_none_dimension_raises_semantic_error():
    """
        Verify that constructing with None embedding_dimension raises SemanticError.
    """
    raised = False
    try:
        StubEmbeddingProvider(provider_name="test", embedding_dimension=None)
    except SemanticError:
        raised = True

    assert raised is True, "None embedding_dimension should raise SemanticError"
    return


# ---- __repr__ and __str__ Tests ----


def test_embeddingprovider_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    provider = StubEmbeddingProvider(
        provider_name="test-provider",
        embedding_dimension=128,
    )

    repr_str = repr(provider)
    has_class = "StubEmbeddingProvider" in repr_str
    assert has_class is True, "repr should contain the class name"
    return


def test_embeddingprovider_repr_contains_provider_name():
    """
        Verify that __repr__ contains the provider name.
    """
    provider = StubEmbeddingProvider(
        provider_name="test-provider",
        embedding_dimension=128,
    )

    repr_str = repr(provider)
    has_name = "test-provider" in repr_str
    assert has_name is True, "repr should contain the provider name"
    return


def test_embeddingprovider_repr_contains_dimension():
    """
        Verify that __repr__ contains the embedding dimension.
    """
    provider = StubEmbeddingProvider(
        provider_name="test-provider",
        embedding_dimension=128,
    )

    repr_str = repr(provider)
    has_dim = "128" in repr_str
    assert has_dim is True, "repr should contain the embedding dimension"
    return


def test_embeddingprovider_str_contains_provider_name():
    """
        Verify that __str__ contains the provider name.
    """
    provider = StubEmbeddingProvider(
        provider_name="test-provider",
        embedding_dimension=256,
    )

    str_val = str(provider)
    has_name = "test-provider" in str_val
    assert has_name is True, "str should contain the provider name"
    return


def test_embeddingprovider_str_contains_dimension():
    """
        Verify that __str__ contains the embedding dimension.
    """
    provider = StubEmbeddingProvider(
        provider_name="test-provider",
        embedding_dimension=256,
    )

    str_val = str(provider)
    has_dim = "256" in str_val
    assert has_dim is True, "str should contain the embedding dimension"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
