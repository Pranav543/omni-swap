import smartpy as sp

class Viewer(sp.Contract):
    def __init__(self):
        self.init(result = sp.none)

    @sp.entry_point
    def receive(self, result):
        self.data.result = sp.some(result)

    @sp.entry_point
    def send(self, fa2Address):
        contract = sp.contract(
            sp.TPair(sp.TUnit, sp.TContract(sp.TNat)),
            fa2Address,
            entry_point = "getTotalSupply"
        ).open_some("Invalid contract")
        sp.transfer((sp.unit, sp.self_entry_point("receive")), sp.mutez(0), contract)

FA = sp.io.import_template("FA1.2.py")

@sp.add_test(name = "Call-getTotalSupply")
def test():
    scenario = sp.test_scenario()
    scenario.h1("FA1.2 Contract")
    token_metadata = {
        "decimals"    : "18",               # Mandatory by the spec
        "name"        : "My Great Token",   # Recommended
        "symbol"      : "MGT",              # Recommended
        # Extra fields
        "icon"        : 'https://smartpy.io/static/img/logo-only.svg'
    }
    contract_metadata = {
        "" : "ipfs://QmaiAUj1FFNGYTu8rLBjc3eeN9cSKwaF8EGMBNDmhzPNFd",
    }
    
    c1 = FA.FA12(
        sp.address("tz1_admin"),
        config              = FA.FA12_config(support_upgradable_metadata = True),
        token_metadata      = token_metadata,
        contract_metadata   = contract_metadata
    )
    scenario += c1

    # Viewer will call getTotalSupply
    c2 = Viewer()
    scenario += c2
    c2.send(c1.address)