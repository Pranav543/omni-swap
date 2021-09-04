import smartpy as sp

# Import FA2 template
FA12 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA1.2.py")
# Define Cover_Token
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


@sp.add_test(name="Fungible Token")
def test():
    scenario = sp.test_scenario()

    admin = sp.test_account("Decentralized Dictator")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")

    # Initialize Cover_Token as cover_token with single_asset = True
    cover_token = Cover_Token(admin.address)
    scenario += cover_token

    scenario.h1("Entry points")
    scenario.h2("Admin mints a few coins")
    cover_token.mint(address=alice.address, value=12).run(sender=admin)
    cover_token.mint(address=alice.address, value=3).run(sender=admin)
    cover_token.mint(address=alice.address, value=3).run(sender=admin)
    scenario.h2("Alice transfers to Bob")
    cover_token.transfer(from_=alice.address, to_=bob.address, value=4).run(
        sender=alice
    )
    scenario.verify(cover_token.data.balances[alice.address].balance == 14)
    scenario.h2("Bob tries to transfer from Alice but he doesn't have her approval")
    cover_token.transfer(from_=alice.address, to_=bob.address, value=4).run(
        sender=bob, valid=False
    )
    scenario.h2("Alice approves Bob and Bob transfers")
    cover_token.approve(spender=bob.address, value=5).run(sender=alice)
    cover_token.transfer(from_=alice.address, to_=bob.address, value=4).run(sender=bob)
    scenario.h2("Bob tries to over-transfer from Alice")
    cover_token.transfer(from_=alice.address, to_=bob.address, value=4).run(
        sender=bob, valid=False
    )
    scenario.h2("Admin burns Bob token")
    cover_token.burn(address=bob.address, value=1).run(sender=admin)
    scenario.verify(cover_token.data.balances[alice.address].balance == 10)
    scenario.h2("Alice tries to burn Bob token")
    cover_token.burn(address=bob.address, value=1).run(sender=alice, valid=False)
    scenario.h2("Admin pauses the contract and Alice cannot transfer anymore")
    cover_token.setPause(True).run(sender=admin)
    cover_token.transfer(from_=alice.address, to_=bob.address, value=4).run(
        sender=alice, valid=False
    )
    scenario.verify(cover_token.data.balances[alice.address].balance == 10)
    scenario.h2("Admin transfers while on pause")
    cover_token.transfer(from_=alice.address, to_=bob.address, value=1).run(
        sender=admin
    )
    scenario.h2("Admin unpauses the contract and transferts are allowed")
    cover_token.setPause(False).run(sender=admin)
    scenario.verify(cover_token.data.balances[alice.address].balance == 9)
    cover_token.transfer(from_=alice.address, to_=bob.address, value=1).run(
        sender=alice
    )

    scenario.verify(cover_token.data.totalSupply == 17)
    scenario.verify(cover_token.data.balances[alice.address].balance == 8)
    scenario.verify(cover_token.data.balances[bob.address].balance == 9)
