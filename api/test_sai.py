#!/usr/bin/env python3
#
# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json

import pkg_resources
from web3 import Web3, EthereumTesterProvider

from api import Address, Wad
from api.approval import directly
from api.auth import DSGuard
from api.feed import DSValue
from api.sai import Tub, Top, Tap
from api.token import DSToken
from api.vault import DSVault


class TestSai():
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.sai = DSToken.deploy(self.web3, 'SAI')
        self.sin = DSToken.deploy(self.web3, 'SIN')
        self.gem = DSToken.deploy(self.web3, 'ETH')
        self.pip = DSValue.deploy(self.web3)
        self.skr = DSToken.deploy(self.web3, 'SKR')
        self.pot = DSVault.deploy(self.web3)
        self.pit = DSVault.deploy(self.web3)
        self.tip = self.deploy('Tip')
        self.dad = DSGuard.deploy(self.web3)
        self.jug = self.deploy('SaiJug', [self.sai.address.address, self.sin.address.address])
        self.jar = self.deploy('SaiJar', [self.skr.address.address, self.gem.address.address, self.pip.address.address])
        self.tub = Tub.deploy(self.web3, Address(self.jar), Address(self.jug), self.pot.address, self.pit.address, Address(self.tip))
        self.tap = Tap.deploy(self.web3, self.tub.address, self.pit.address)
        self.top = Top.deploy(self.web3, self.tub.address, self.tap.address)

        self.sai.set_authority(self.dad.address)
        self.sin.set_authority(self.dad.address)
        self.skr.set_authority(self.dad.address)
        self.pot.set_authority(self.dad.address)
        self.pit.set_authority(self.dad.address)
        self.tub.set_authority(self.dad.address)
        self.tap.set_authority(self.dad.address)
        self.top.set_authority(self.dad.address)


        # seth send $SAI_TIP "warp(uint64)" 0


        self.dad.permit(self.tub.address, Address(self.jug), DSGuard.ANY_SIG)
        self.dad.permit(self.tub.address, self.pot.address, DSGuard.ANY_SIG)

        self.dad.permit(self.tap.address, Address(self.jug), DSGuard.ANY_SIG)
        self.dad.permit(self.tap.address, self.pit.address, DSGuard.ANY_SIG)

        self.dad.permit(self.top.address, Address(self.jug), DSGuard.ANY_SIG)
        self.dad.permit(self.top.address, self.pit.address, DSGuard.ANY_SIG)

        self.dad.permit(Address(self.jar), self.skr.address, DSGuard.ANY_SIG)

        self.dad.permit(Address(self.jug), self.pot.address, DSGuard.ANY_SIG)
        self.dad.permit(Address(self.jug), self.pit.address, DSGuard.ANY_SIG)

        self.dad.permit(self.pot.address, self.sai.address, DSGuard.ANY_SIG)
        self.dad.permit(self.pot.address, self.sin.address, DSGuard.ANY_SIG)

        self.dad.permit(self.pit.address, self.sai.address, DSGuard.ANY_SIG)
        self.dad.permit(self.pit.address, self.sin.address, DSGuard.ANY_SIG)

        self.dad.permit(self.tub.address, self.tub.jar(), DSGuard.ANY_SIG)
        self.dad.permit(self.top.address, self.tub.jar(), DSGuard.ANY_SIG)
        self.dad.permit(self.top.address, self.tub.address, DSGuard.ANY_SIG)



        print(self.gem.balance_of(self.our_address))
        self.gem.mint(Wad.from_number(10))
        print(self.gem.balance_of(self.our_address))

        self.tub.approve(directly())

    def deploy(self, contract_name, args=None):
        contract_factory = self.web3.eth.contract(abi=json.loads(pkg_resources.resource_string('api.feed', f'abi/{contract_name}.abi')),
                                     bytecode=pkg_resources.resource_string('api.feed', f'abi/{contract_name}.bin'))
        tx_hash = contract_factory.deploy(args=args)
        receipt = self.web3.eth.getTransactionReceipt(tx_hash)
        return receipt['contractAddress']

    def test_join_and_exit(self):
        # given
        assert self.skr.balance_of(self.our_address) == Wad(0)
        assert self.skr.total_supply() == Wad(0)

        # when
        print(self.tub.join(Wad.from_number(5)))

        # then
        assert self.skr.balance_of(self.our_address) == Wad.from_number(5)
        assert self.skr.total_supply() == Wad.from_number(5)

        # when
        print(self.tub.exit(Wad.from_number(4)))

        # then
        assert self.skr.balance_of(self.our_address) == Wad.from_number(1)
        assert self.skr.total_supply() == Wad.from_number(1)
