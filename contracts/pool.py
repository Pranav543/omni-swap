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

    @sp.global_lambda
    def calculateCoverTokenAmount(x):
        sp.result(x * 1)

    def buyCoverageInternal(self, buyer, premiumAmount):
        sp.transfer(
            sp.record(from_=buyer, to_=sp.to_address(sp.self), value=premiumAmount),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )
        sp.data.premiumPool += premiumAmount
        coverTokenAmount = self.calculateCoverTokenAmount(premiumAmount)
        sp.transfer(
            sp.record(address=buyer, value=coverTokenAmount),
            sp.tez(5),
            sp.contract(
                sp.TRecord(address=sp.TAddress, value=sp.TNat),
                self.data.coverToken,
                "mint",
            ).open_some(),
        )

    @sp.entry_point
    def buyCoverage(self, params):
        self.buyCoverageInternal(sp.sender, params.premiumAmount)

    @sp.global_lambda
    def calculateCoverTokenValue(self, coverTokenAmount_, totalCoverTokenSupply_):
        coveragePoolSize_ = self.getCoveragePool()
        coverTokenValueTemp_ = coveragePoolSize_ * 100 / totalCoverTokenSupply_
        coverTokenValue_ = coverTokenAmount_ * coverTokenValueTemp_ / 100
        sp.result(coverTokenValue_)

    @sp.entry_point
    def claimCoverage(self, params):
        coverageAmount = self.calculateCoverTokenValue(
            params.coverTokenAmount, params.totalCoverTokenSupply
        )
        sp.transfer(
            sp.record(
                from_=sp.to_address(sp.self), to_=sp.sender, value=coverageAmount
            ),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )

        sp.transfer(
            sp.record(address=sp.sender, value=params.coverTokenAmount),
            sp.tez(5),
            sp.contract(
                sp.TRecord(address=sp.TAddress, value=sp.TNat),
                self.data.coverToken,
                "burn",
            ).open_some(),
        )

    @sp.global_lambda
    def calculatePremiumTokenAmount(x):
        sp.result(x * 1)

    def sellCoverageInternal(self, seller, coverageAmount):
        sp.transfer(
            sp.record(from_=seller, to_=sp.to_address(sp.self), value=coverageAmount),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )
        sp.data.coveragePool += coverageAmount
        premiumTokenAmount = self.calculatePremiumTokenAmount(coverageAmount)
        sp.transfer(
            sp.record(address=seller, value=premiumTokenAmount),
            sp.tez(5),
            sp.contract(
                sp.TRecord(address=sp.TAddress, value=sp.TNat),
                self.data.coverToken,
                "mint",
            ).open_some(),
        )

    @sp.entry_point
    def sellCoverage(self, params):
        self.sellCoverageInternal(sp.sender, params.coverageAmount)

    @sp.global_lambda
    def calculatePremiumTokenValue(self, premiumTokenAmount_, totalPremiumTokenSupply_):
        premiumPoolSize_ = self.getPremiumPool()
        premiumTokenValueTemp_ = premiumPoolSize_ * 100 / totalPremiumTokenSupply_
        premiumTokenValue_ = premiumTokenAmount_ * premiumTokenValueTemp_ / 100
        sp.result(premiumTokenValue_)

    @sp.entry_point
    def withdrawPremium(self, params):
        sp.verify(sp.data.isExpired == True, message="Error: CDS Is Not Expired Yet!")
        premiumAmount = self.calculatePremiumTokenValue(params.premiumTokenAmount)
        sp.transfer(
            sp.record(from_=sp.to_address(sp.self), to_=sp.sender, value=premiumAmount),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )
        sp.data.premiumPool -= premiumAmount
        sp.transfer(
            sp.record(address=sp.sender, value=params.premiumTokenAmount),
            sp.tez(5),
            sp.contract(
                sp.TRecord(address=sp.TAddress, value=sp.TNat),
                self.data.premiumToken,
                "burn",
            ).open_some(),
        )

    @sp.entry_point
    def withdrawCoverage(self, params):
        sp.verify(sp.data.isExpired == True, message="Error: CDS Is Not Expired Yet!")
        sp.transfer(
            sp.record(
                from_=sp.to_address(sp.self), to_=sp.sender, value=params.coverageAmount
            ),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )
        sp.data.coveragePool -= params.coverageAmount
