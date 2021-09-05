import smartpy as sp

# Import FA2 template
FA12 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA1.2.py")
# Define Premium_Token
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
        sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat))
        self.addAddressIfNecessary(params.address)
        self.data.balances[params.address].balance += params.value
        self.data.totalSupply += params.value

    @sp.entry_point
    def burn(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat))
        sp.verify(self.data.balances[params.address].balance >= params.value, message="Error: InsufficientBalance")
        self.data.balances[params.address].balance = sp.as_nat(self.data.balances[params.address].balance - params.value)
        self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.value)


@sp.add_test(name="Fungible Token")
def test():
    scenario = sp.test_scenario()

    admin = sp.test_account("Decentralized Dictator")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")

    # Initialize Premium_Token as premium_token with single_asset = True
    premium_token = Premium_Token(admin.address)
    scenario += premium_token

    scenario.h1("Entry points")
    scenario.h2("Admin mints a few coins")
    premium_token.mint(address=alice.address, value=12).run(sender=admin)
    premium_token.mint(address=alice.address, value=3).run(sender=admin)
    premium_token.mint(address=alice.address, value=3).run(sender=admin)
    scenario.h2("Alice transfers to Bob")
    premium_token.transfer(from_=alice.address, to_=bob.address, value=4).run(
        sender=alice
    )
    scenario.verify(premium_token.data.balances[alice.address].balance == 14)
    scenario.h2("Bob tries to transfer from Alice but he doesn't have her approval")
    premium_token.transfer(from_=alice.address, to_=bob.address, value=4).run(
        sender=bob, valid=False
    )
    scenario.h2("Alice approves Bob and Bob transfers")
    premium_token.approve(spender=bob.address, value=5).run(sender=alice)
    premium_token.transfer(from_=alice.address, to_=bob.address, value=4).run(
        sender=bob
    )
    scenario.h2("Bob tries to over-transfer from Alice")
    premium_token.transfer(from_=alice.address, to_=bob.address, value=4).run(
        sender=bob, valid=False
    )
    scenario.h2("Admin burns Bob token")
    premium_token.burn(address=bob.address, value=1).run(sender=admin)
    scenario.verify(premium_token.data.balances[alice.address].balance == 10)
    scenario.h2("Alice tries to burn Bob token")
    premium_token.burn(address=bob.address, value=1).run(sender=alice, valid=False)
    scenario.h2("Admin pauses the contract and Alice cannot transfer anymore")
    premium_token.setPause(True).run(sender=admin)
    premium_token.transfer(from_=alice.address, to_=bob.address, value=4).run(
        sender=alice, valid=False
    )
    scenario.verify(premium_token.data.balances[alice.address].balance == 10)
    scenario.h2("Admin transfers while on pause")
    premium_token.transfer(from_=alice.address, to_=bob.address, value=1).run(
        sender=admin
    )
    scenario.h2("Admin unpauses the contract and transferts are allowed")
    premium_token.setPause(False).run(sender=admin)
    scenario.verify(premium_token.data.balances[alice.address].balance == 9)
    premium_token.transfer(from_=alice.address, to_=bob.address, value=1).run(
        sender=alice
    )

    scenario.verify(premium_token.data.totalSupply == 17)
    scenario.verify(premium_token.data.balances[alice.address].balance == 8)
    scenario.verify(premium_token.data.balances[bob.address].balance == 9)
