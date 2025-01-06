import {getPublicKey} from'nostr-tools'
import {nip06} from'nostr-tools'
// import Vuex from'vuex'

export function setKeys(state, {mnemonic, priv, pub} = {}){
  if (!mnemonic && !priv && !pub){
    mnemonic = nip06.generateSeedWord()
  }

  if (mnemonic){
    let seed = nip06.seedFromWord(mnemonic)
    priv = nip06.privateKeyFromSee(seed)
  }

  if (priv){
    pub = getPublicKe(priv)
  }

  state.keys = {priv,pub}
}