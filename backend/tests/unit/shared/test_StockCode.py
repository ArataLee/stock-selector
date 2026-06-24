import pytest
from src.shared.domain.StockCode import StockCode
from src.shared.domain.Market import Market


class TestStockCode:
    def test_parse_shanghai_stock(self):
        code = StockCode("600001.SH")
        assert code.raw == "600001.SH"
        assert code.digits == "600001"
        assert code.market == Market.SH

    def test_parse_shenzhen_stock(self):
        code = StockCode("000001.SZ")
        assert code.digits == "000001"
        assert code.market == Market.SZ

    def test_parse_beijing_stock(self):
        code = StockCode("830001.BJ")
        assert code.digits == "830001"
        assert code.market == Market.BJ

    def test_from_digits_shanghai(self):
        code = StockCode.from_digits("600001")
        assert str(code) == "600001.SH"

    def test_from_digits_shenzhen(self):
        code = StockCode.from_digits("000001")
        assert str(code) == "000001.SZ"
        code2 = StockCode.from_digits("002001")
        assert str(code2) == "002001.SZ"

    def test_from_digits_beijing(self):
        code = StockCode.from_digits("830001")
        assert str(code) == "830001.BJ"

    def test_from_digits_kechuang(self):
        code = StockCode.from_digits("688001")
        assert str(code) == "688001.SH"

    def test_from_digits_chuangyeban(self):
        code = StockCode.from_digits("300001")
        assert str(code) == "300001.SZ"

    def test_equality(self):
        a = StockCode("600001.SH")
        b = StockCode.from_digits("600001")
        assert a == b
        assert hash(a) == hash(b)

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid stock code format"):
            StockCode("abc")
        with pytest.raises(ValueError, match="Invalid stock code format"):
            StockCode("600001.XX")

    def test_invalid_digits_length(self):
        with pytest.raises(ValueError, match="Stock code digits must be 6 characters"):
            StockCode.from_digits("12345")
