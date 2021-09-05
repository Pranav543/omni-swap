import smartpy as sp

# Import FA2 template
FA12 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA1.2.py")


class Cover_Token(FA12.FA12):
    def __init__(self, admin_address):
        super().__init__(
            admin_address,
            config=FA12.FA12_config(support_upgradable_metadata=True),
            token_metadata={
                "decimals": "18",  # Mandatory by the spec
                "name": "Cover Token",  # Recommended
                "symbol": "CT",  # Recommended
            },
        )

    @sp.entry_point
    def mint(self, params):
        sp.set_type(params, sp.TRecord(address=sp.TAddress, value=sp.TNat))
        self.addAddressIfNecessary(params.address)
        self.data.balances[params.address].balance += params.value
        self.data.totalSupply += params.value

    @sp.entry_point
    def burn(self, params):
        sp.set_type(params, sp.TRecord(address=sp.TAddress, value=sp.TNat))
        sp.verify(
            self.data.balances[params.address].balance >= params.value,
            message="Error: InsufficientBalance",
        )
        self.data.balances[params.address].balance = sp.as_nat(
            self.data.balances[params.address].balance - params.value
        )
        self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.value)


class Premium_Token(FA12.FA12):
    def __init__(self, admin_address):
        super().__init__(
            admin_address,
            config=FA12.FA12_config(support_upgradable_metadata=True),
            token_metadata={
                "decimals": "18",  # Mandatory by the spec
                "name": "Premium Token",  # Recommended
                "symbol": "PT",  # Recommended
            },
        )

    @sp.entry_point
    def mint(self, params):
        sp.set_type(params, sp.TRecord(address=sp.TAddress, value=sp.TNat))
        self.addAddressIfNecessary(params.address)
        self.data.balances[params.address].balance += params.value
        self.data.totalSupply += params.value

    @sp.entry_point
    def burn(self, params):
        sp.set_type(params, sp.TRecord(address=sp.TAddress, value=sp.TNat))
        sp.verify(
            self.data.balances[params.address].balance >= params.value,
            message="Error: InsufficientBalance",
        )
        self.data.balances[params.address].balance = sp.as_nat(
            self.data.balances[params.address].balance - params.value
        )
        self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.value)


class Payment_Token(FA12.FA12):
    def __init__(self, admin_address):
        super().__init__(
            admin_address,
            config=FA12.FA12_config(support_upgradable_metadata=True),
            token_metadata={
                "decimals": "18",  # Mandatory by the spec
                "name": "Payment Token",  # Recommended
                "symbol": "DAI",  # Recommended
            },
        )

    @sp.entry_point
    def mint(self, params):
        sp.set_type(params, sp.TRecord(address=sp.TAddress, value=sp.TNat))
        self.addAddressIfNecessary(params.address)
        self.data.balances[params.address].balance += params.value
        self.data.totalSupply += params.value

    @sp.entry_point
    def burn(self, params):
        sp.set_type(params, sp.TRecord(address=sp.TAddress, value=sp.TNat))
        sp.verify(
            self.data.balances[params.address].balance >= params.value,
            message="Error: InsufficientBalance",
        )
        self.data.balances[params.address].balance = sp.as_nat(
            self.data.balances[params.address].balance - params.value
        )
        self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.value)


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
            totalPremiumTokenSupply=sp.int(100000000),
            totalCoverTokenSupply=sp.int(100000000),
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
        self.data.totalPremiumTokenSupply = sp.to_int(result)

    @sp.entry_point
    def receiveTotalCoverTokenSupply(self, result):
        self.data.totalCoverTokenSupply = sp.to_int(result)

    @sp.entry_point
    def setIsExpiredTrueForTesting(self):
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
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat).layout(
                    ("from_ as from", ("to_ as to", "value"))
                ),
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
                totalCoverTokenSupply_=sp.as_nat(self.data.totalCoverTokenSupply),
                coveragePoolSize_=self.data.coveragePool,
            )
        )
        sp.transfer(
            sp.record(
                from_=sp.to_address(sp.self), to_=sp.sender, value=coverageAmount.value
            ),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat).layout(
                    ("from_ as from", ("to_ as to", "value"))
                ),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )

        self.data.coveragePool = sp.as_nat(
            self.data.coveragePool - coverageAmount.value, message=None
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
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat).layout(
                    ("from_ as from", ("to_ as to", "value"))
                ),
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
                self.data.premiumToken,
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

        premiumAmount = sp.local("premiumAmount", 0)
        premiumPoolSize_ = sp.local("premiumPoolSize_", 0)
        premiumPoolSize_.value = self.data.premiumPool
        totalPremiumTokenSupply_ = sp.as_nat(self.data.totalPremiumTokenSupply)
        premiumAmount.value = self.calculatePremiumTokenValue(
            sp.record(
                premiumTokenAmount_=params.premiumTokenAmount,
                premiumPoolSize_=self.data.premiumPool,
                totalPremiumTokenSupply=sp.as_nat(self.data.totalPremiumTokenSupply),
            )
        )
        sp.transfer(
            sp.record(
                from_=sp.to_address(sp.self), to_=sp.sender, value=premiumAmount.value
            ),
            sp.tez(0),
            sp.contract(
                sp.TRecord(from_=sp.TAddress, to_=sp.TAddress, value=sp.TNat).layout(
                    ("from_ as from", ("to_ as to", "value"))
                ),
                self.data.paymentToken,
                "transfer",
            ).open_some(),
        )
        self.data.premiumPool = sp.as_nat(
            self.data.premiumPool - premiumAmount.value, message=None
        )
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

    @sp.entry_point
    def setPremiumTokenSupply(self):
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

    @sp.entry_point
    def setCoverTokenSupply(self):
        coverContract = sp.contract(
            sp.TPair(sp.TUnit, sp.TContract(sp.TNat)),
            self.data.coverToken,
            entry_point="getTotalSupply",
        ).open_some("Invalid contract")
        sp.transfer(
            (sp.unit, sp.self_entry_point("receiveTotalCoverTokenSupply")),
            sp.mutez(0),
            coverContract,
        )


@sp.add_test(name="OmniSwap")
def test():
    scenario = sp.test_scenario()
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")
    admin = sp.test_account("admin")

    premium_token = Premium_Token(admin.address)
    cover_token = Cover_Token(admin.address)
    payment_token = Payment_Token(admin.address)

    scenario += premium_token
    scenario += cover_token
    scenario += payment_token

    scenario.h2("All mint DAI")
    scenario += payment_token.mint(address=admin.address, value=1000).run(sender=admin)
    scenario += payment_token.mint(address=alice.address, value=1000).run(sender=admin)
    scenario += payment_token.mint(address=bob.address, value=1000).run(sender=alice)

    scenario.h3("Initialize Pool Contract")
    pool = Pool(
        payment_token.address, cover_token.address, premium_token.address, 1630842340
    )
    scenario += pool

    scenario.h3("Alice buys coverage gets cover token")
    scenario += payment_token.approve(spender=pool.address, value=10000).run(
        sender=alice
    )
    scenario += pool.buyCoverage(premiumAmount=sp.nat(500)).run(sender=alice)
    scenario.verify(payment_token.data.balances[alice.address].balance == 500)
    scenario.show(cover_token.data.balances[alice.address].balance)

    scenario.h3("Bob sells coverage gets prem token")
    scenario += payment_token.approve(spender=pool.address, value=10000).run(sender=bob)
    scenario += pool.sellCoverage(coverageAmount=500).run(sender=bob)
    scenario.verify(payment_token.data.balances[bob.address].balance == 500)
    scenario.show(premium_token.data.balances[bob.address].balance)

    scenario.show(pool.data.isExpired)

    scenario.h2("Bob claims in case of no default")
    scenario.h3("Bob's DAI")
    scenario.show(payment_token.data.balances[bob.address].balance)
    scenario.h3("Bob's Prem")
    scenario.show(premium_token.data.balances[bob.address].balance)
    scenario.h3("isExpired = True")
    scenario += pool.setIsExpiredTrueForTesting().run(sender=bob)

    scenario.show(pool.data.isExpired)

    scenario += pool.setCoverTokenSupply().run(sender=alice)
    scenario += pool.setPremiumTokenSupply().run(sender=alice)

    scenario += pool.withdrawPremium(premiumTokenAmount=500).run(sender=bob)
    scenario.h3("Bob's DAI")
    scenario.show(payment_token.data.balances[bob.address].balance)
    scenario.h3("Bob's Prem")
    scenario.show(premium_token.data.balances[bob.address].balance)
    scenario.show(pool.data.premiumPool)

    # scenario.h2("Alice claims in case of default")
    # scenario.h3("Alice's DAI")
    # scenario.show(payment_token.data.balances[alice.address].balance)
    # scenario.h3("Alice's Cover")
    # scenario.show(cover_token.data.balances[alice.address].balance)

    # scenario += pool.claimCoverage(coverTokenAmount=500).run(sender=alice)
    # scenario.h3("Alice's DAI")
    # scenario.show(payment_token.data.balances[alice.address].balance)
    # scenario.h3("Alice's Cover")
    # scenario.show(cover_token.data.balances[alice.address].balance)
    # scenario.show(pool.data.coveragePool)
