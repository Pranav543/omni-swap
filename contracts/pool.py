class Pool(sp.Contract):
    def __init__(
        self,
        _paymentToken,
        _coverToken,
        _premiumToken,
        _expiryTimestamp,
    ):
        self.init(
            paymentToken=_paymentToken,
            coverToken=_coverToken,
            premiumToken=_premiumToken,
            expiryTimestamp=sp.timestamp(_expiryTimestamp),
            coveragePool=sp.nat(0),
            premiumPool=sp.nat(0),
            isExpired=False,
            totalPremiumTokenSupply=sp.none,
        )

    # @sp.utils.view(sp.timestamp)
    # def getExpirationTimestamp(self):
    #     sp.result(self.data.expiryTimestamp)

    # @sp.utils.view(sp.TNat)
    # def getCoveragePool(self, params):
    #     sp.result(self.data.coveragePool)

    # @sp.utils.view(sp.TNat)
    # def getPremiumPool(self, params):
    #     sp.result(self.data.premiumPool)

    @sp.entry_point
    def setIsExpiredTrue(self):
        sp.verify(
            sp.now > self.data.expiryTimestamp, message="Error: CDS Is Not Expired Yet!"
        )
        self.data.isExpired = True

    @sp.entry_point
    def receiveTotalPremiumTokenSupply(self, result):
        self.data.totalPremiumTokenSupply = sp.some(sp.to_int(result))

    @sp.entry_point
    def setIsExpiredTrueForTesting(self):
        sp.verify(
            sp.now > self.data.expiryTimestamp, message="Error: CDS Is Not Expired Yet!"
        )
        self.data.isExpired = True

    # @sp.global_lambda
    # def calculateCoverTokenAmount(x):
    #     sp.result(x * 1)

    @sp.sub_entry_point
    def buyCoverageInternal(self, params):
        sp.transfer(
            sp.record(
                from_=params.buyer,
                to_=sp.to_address(sp.self),
                value=params.premiumAmount,
            ),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )
        self.data.premiumPool = self.data.premiumPool + params.premiumAmount
        coverTokenAmount = sp.local("coverTokenAmount", 0)
        coverTokenAmount.value = params.premiumAmount
        sp.transfer(
            sp.record(address=params.buyer, value=coverTokenAmount.value),
            sp.tez(0),
            sp.contract(
                sp.TRecord(address=sp.TAddress, value=sp.TNat),
                self.data.coverToken,
                "mint",
            ).open_some(),
        )

    @sp.entry_point
    def buyCoverage(self, params):
        self.buyCoverageInternal(
            sp.record(buyer=sp.sender, premiumAmount=params.premiumAmount)
        )

    @sp.global_lambda
    def calculateCoverTokenValue(params):
        coverTokenValueTemp_ = sp.local("coverTokenValueTemp_", 0)
        coverTokenValue_ = sp.local("coverTokenValue_", 0)
        coverTokenValueTemp_.value = (
            params.coveragePoolSize_ * 100 / params.totalCoverTokenSupply_
        )
        coverTokenValue_.value = (
            params.coverTokenAmount_ * coverTokenValueTemp_.value / 100
        )
        sp.result(coverTokenValue_.value)

    @sp.entry_point
    def claimCoverage(self, params):
        coverageAmount = sp.local("coverageAmount", 0)
        coveragePoolSize_ = sp.local("coveragePoolSize_", 0)
        coveragePoolSize_.value = self.data.coveragePool
        coverageAmount.value = self.calculateCoverTokenValue(
            sp.record(
                coverTokenAmount_=params.coverTokenAmount,
                totalCoverTokenSupply_=params.totalCoverTokenSupply,
                coveragePoolSize_=self.data.coveragePool,
            )
        )
        sp.transfer(
            sp.record(
                from_=sp.to_address(sp.self), to_=sp.sender, value=coverageAmount.value
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
            sp.tez(0),
            sp.contract(
                sp.TRecord(address=sp.TAddress, value=sp.TNat),
                self.data.coverToken,
                "burn",
            ).open_some(),
        )

    @sp.global_lambda
    def calculatePremiumTokenAmount(x):
        sp.result(x * 1)

    @sp.sub_entry_point
    def sellCoverageInternal(self, params):
        sp.transfer(
            sp.record(
                from_=params.seller,
                to_=sp.to_address(sp.self),
                value=params.coverageAmount,
            ),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )
        self.data.coveragePool += params.coverageAmount
        premiumTokenAmount = sp.local("premiumTokenAmount", 0)
        premiumTokenAmount.value = params.coverageAmount

        sp.transfer(
            sp.record(address=params.seller, value=premiumTokenAmount.value),
            sp.tez(0),
            sp.contract(
                sp.TRecord(address=sp.TAddress, value=sp.TNat),
                self.data.coverToken,
                "mint",
            ).open_some(),
        )

    @sp.entry_point
    def sellCoverage(self, params):
        self.sellCoverageInternal(
            sp.record(seller=sp.sender, coverageAmount=params.coverageAmount)
        )

    @sp.global_lambda
    def calculatePremiumTokenValue(params):
        premiumTokenValueTemp_ = sp.local("premiumTokenValueTemp_", 0)
        premiumTokenValue_ = sp.local("premiumTokenValue_", 0)
        premiumTokenValueTemp_.value = (
            params.premiumPoolSize_ * 100 / params.totalPremiumTokenSupply
        )
        premiumTokenValue_.value = (
            params.premiumTokenAmount_ * premiumTokenValueTemp_.value / 100
        )
        sp.result(premiumTokenValue_.value)

    @sp.entry_point
    def withdrawPremium(self, params):
        sp.verify(self.data.isExpired == True, message="Error: CDS Is Not Expired Yet!")

        premiumContract = sp.contract(
            sp.TPair(sp.TUnit, sp.TContract(sp.TNat)),
            self.data.premiumToken,
            entry_point="getTotalSupply",
        ).open_some("Invalid contract")
        sp.transfer(
            (sp.unit, sp.self_entry_point("receiveTotalPremiumTokenSupply")),
            sp.mutez(0),
            premiumContract,
        )

        premiumAmount = sp.local("premiumAmount", 0)
        premiumPoolSize_ = sp.local("premiumPoolSize_", 0)
        premiumPoolSize_.value = self.data.premiumPool
        totalPremiumTokenSupply_ = self.data.totalPremiumTokenSupply.open_some()
        premiumAmount.value = self.calculatePremiumTokenValue(
            sp.record(
                premiumTokenAmount_=params.premiumToken,
                premiumPoolSize_=self.data.premiumPool,
                totalPremiumTokenSupply=sp.as_nat(totalPremiumTokenSupply_),
            )
        )
        sp.transfer(
            sp.record(
                from_=sp.to_address(sp.self), to_=sp.sender, value=premiumAmount.value
            ),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )
        self.data.premiumPool = sp.as_nat(self.data.premiumPool - premiumAmount.value)
        sp.transfer(
            sp.record(address=sp.sender, value=params.premiumTokenAmount),
            sp.tez(0),
            sp.contract(
                sp.TRecord(address=sp.TAddress, value=sp.TNat),
                self.data.premiumToken,
                "burn",
            ).open_some(),
        )

    @sp.entry_point
    def withdrawCoverage(self, params):
        sp.verify(self.data.isExpired == True, message="Error: CDS Is Not Expired Yet!")
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
        self.data.coveragePool = sp.as_nat(
            self.data.coveragePool - params.coverageAmount
        )