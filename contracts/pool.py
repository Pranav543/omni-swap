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

    @sp.utils.view(sp.timestamp)
    def getExpirationTimestamp(self):
        sp.result(self.data.expiryTimestamp)

    @sp.utils.view(sp.TNat)
    def getCoveragePool(self):
        sp.result(self.data.coveragePool)

    @sp.utils.view(sp.TNat)
    def getPremiumPool(self):
        sp.result(self.data.premiumPool)

    @sp.entry_point
    def setIsExpiredTrue(self):
        sp.verify(
            sp.now > self.data.expiryTimestamp, message="Error: CDS Is Not Expired Yet!"
        )
        self.data.isExpired = True

    @sp.entry_point
    def setIsExpiredTrueForTesting(self):
        sp.verify(
            sp.now > self.data.expiryTimestamp, message="Error: CDS Is Not Expired Yet!"
        )
        self.data.isExpired = True

    @sp.entry_point
    def buyCoverage(self, params):
        self.buyCoverageInternal(sp.sender, params.premiumAmount)
