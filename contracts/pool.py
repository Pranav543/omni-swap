import smartpy as sp


class Pool(sp.Contract):
    def __init__(
        self,
        _paymentToken,
        _coverToken,
        _premiumToken,
        _sampleMapleLoanContract,
        _expiryTimestamp,
    ):
        self.init(
            paymentToken=_paymentToken,
            coverToken=_coverToken,
            premiumToken=_premiumToken,
            sampleMapleLoanContract=_sampleMapleLoanContract,
            expiryTimestamp=sp.timestamp(_expiryTimestamp),
            coveragePool=sp.nat(0),
            premiumPool=sp.nat(0),
            isExpired=False,
        )
