// Research reference benchmark for the current FedQSec four-response construction.
// Not a constant-time or production-hardened cryptographic implementation.
#include <openssl/evp.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
using Bytes=std::vector<uint8_t>;
using Poly=std::vector<int32_t>;
using Spectrum=std::vector<uint32_t>;
static volatile uint64_t sink_value=0;
static void require(bool b,const std::string& s){if(!b)throw std::runtime_error(s);}
static void u32(Bytes& b,uint32_t x){for(int j=0;j<4;++j)b.push_back(uint8_t(x>>(8*j)));}
static void u64(Bytes& b,uint64_t x){for(int j=0;j<8;++j)b.push_back(uint8_t(x>>(8*j)));}
static void field(Bytes& b,const Bytes& x){u64(b,x.size());b.insert(b.end(),x.begin(),x.end());}
static void textfield(Bytes& b,const std::string& s){field(b,Bytes(s.begin(),s.end()));}
static void polyfield(Bytes& b,const Poly& p){u64(b,p.size());for(auto x:p)u32(b,uint32_t(x));}
static void rawpoly(Bytes& b,const Poly& p){for(auto x:p)u32(b,uint32_t(x));}
static Poly readpoly(const Bytes& b,size_t& pos,int d){
 require(pos+size_t(d)*4<=b.size(),"short polynomial encoding");Poly p(d);
 for(auto& x:p){uint32_t w=0;for(int j=0;j<4;++j)w|=uint32_t(b[pos++])<<(8*j);x=int32_t(w);}return p;
}
static Bytes shake(const Bytes& input,size_t length){
 Bytes out(length);EVP_MD_CTX* c=EVP_MD_CTX_new();require(c,"EVP_MD_CTX_new");
 bool ok=EVP_DigestInit_ex(c,EVP_shake256(),nullptr)==1 && EVP_DigestUpdate(c,input.data(),input.size())==1 && EVP_DigestFinalXOF(c,out.data(),out.size())==1;
 EVP_MD_CTX_free(c);require(ok,"SHAKE256 failure");return out;
}
struct Reader{
 Bytes input,data;size_t pos=0;
 explicit Reader(Bytes b,size_t n=512):input(std::move(b)),data(shake(input,n)){}
 uint32_t next(){if(pos+4>data.size())data=shake(input,data.size()*2);uint32_t x=0;for(int j=0;j<4;++j)x|=uint32_t(data[pos++])<<(8*j);return x;}
 uint32_t below(uint32_t n){uint64_t lim=(uint64_t(1)<<32)/n*n;uint32_t x;do{x=next();}while(uint64_t(x)>=lim);return x%n;}
};
// AES-256-CTR stream with a reproducible benchmark seed (not production key seeding).
struct RNG{
 EVP_CIPHER_CTX* ctx=nullptr;std::array<uint8_t,8192> buf{},zero{};size_t pos=8192;
 explicit RNG(uint64_t seed){Bytes b; textfield(b,"FedQSec benchmark seed");u64(b,seed);auto k=shake(b,48);ctx=EVP_CIPHER_CTX_new();require(ctx,"AES ctx");require(EVP_EncryptInit_ex(ctx,EVP_aes_256_ctr(),nullptr,k.data(),k.data()+32)==1,"AES init");}
 ~RNG(){EVP_CIPHER_CTX_free(ctx);}RNG(const RNG&)=delete;
 uint64_t next(){if(pos+8>buf.size()){int n=0;require(EVP_EncryptUpdate(ctx,buf.data(),&n,zero.data(),zero.size())==1 && n==int(buf.size()),"AES stream");pos=0;}uint64_t x=0;for(int j=0;j<8;++j)x|=uint64_t(buf[pos++])<<(8*j);return x;}
 double uniform(){return double(next()>>11)*0x1.0p-53;}
 uint32_t below(uint32_t n){uint64_t lim=UINT64_MAX-UINT64_MAX%n;uint64_t x;do{x=next();}while(x>=lim);return x%n;}
 Bytes bytes(size_t n){Bytes b(n);for(size_t i=0;i<n;){auto x=next();for(int j=0;j<8 && i<n;++j)b[i++]=uint8_t(x>>(8*j));}return b;}
};
struct Gaussian{
 double sigma;std::vector<double> cdf;
 explicit Gaussian(double s):sigma(s){
  int cut=int(std::ceil(14*s));cdf.resize(cut+1);long double total=1;
  cdf[0]=1;for(int k=1;k<=cut;++k){total+=2*std::exp(-0.5L*k*k/(s*s));cdf[k]=double(total);}
  for(auto& x:cdf){x=double((long double)x/total);}cdf.back()=1;
 }
 int32_t sample(RNG& r)const{double u=r.uniform();auto k=int32_t(std::lower_bound(cdf.begin(),cdf.end(),u)-cdf.begin());return k && (r.next()&1)?-k:k;}
 Poly samplepoly(RNG& r,int d)const{Poly p(d);for(auto& x:p)x=sample(r);return p;}
};
static uint32_t powmod(uint32_t a,uint64_t e,uint32_t q){uint64_t x=1;while(e){if(e&1)x=x*a%q;a=uint64_t(a)*a%q;e>>=1;}return uint32_t(x);}
static uint32_t primitive_root(uint32_t q){uint32_t t=q-1;std::vector<uint32_t> f;for(uint32_t p=2;uint64_t(p)*p<=t;++p)if(t%p==0){f.push_back(p);while(t%p==0)t/=p;}if(t>1)f.push_back(t);for(uint32_t g=2;;++g){bool ok=true;for(auto p:f)if(powmod(g,(q-1)/p,q)==1){ok=false;break;}if(ok)return g;}}
struct Profile{int index,d,m;uint32_t q;double sigma,sy;int omega;};
static const Profile profiles[]={{1,1024,2048,2101249,1.1,19114,16},{2,1536,4608,10418689,1.5,77484,24},{3,2048,4096,14012417,1.9,90462,31}};
struct Ring{
 Profile p;Spectrum roots,invroots;uint32_t invn;
 explicit Ring(Profile a):p(a),roots(a.m),invroots(a.m){
  require((p.q-1)%p.m==0,"modulus has no required roots");auto w=powmod(primitive_root(p.q),(p.q-1)/p.m,p.q),wi=powmod(w,p.q-2,p.q);
  roots[0]=invroots[0]=1;for(int i=1;i<p.m;++i){roots[i]=uint64_t(roots[i-1])*w%p.q;invroots[i]=uint64_t(invroots[i-1])*wi%p.q;}invn=powmod(p.m,p.q-2,p.q);
 }
 uint32_t mod(int64_t x)const{x%=p.q;if(x<0)x+=p.q;return uint32_t(x);}
 int32_t center(int64_t x)const{uint32_t w=mod(x);return w>p.q/2?int32_t(w)-int32_t(p.q):int32_t(w);}
 uint32_t add(uint32_t a,uint32_t b)const{uint32_t s=a+b;return s>=p.q?s-p.q:s;}
 uint32_t sub(uint32_t a,uint32_t b)const{return a>=b?a-b:a+p.q-b;}
 void fft(const uint32_t* a,size_t stride,uint32_t* out,int n,int step,const Spectrum& rt)const{
  if(n==1){out[0]=a[0];return;}int r=n%3==0?3:2,s=n/r;
  for(int j=0;j<r;++j)fft(a+j*stride,stride*r,out+j*s,s,step*r,rt);
  if(r==2){for(int t=0;t<s;++t){uint32_t x=out[t],y=uint64_t(out[t+s])*rt[t*step]%p.q;out[t]=add(x,y);out[t+s]=sub(x,y);}}
  else{uint32_t z=rt[p.m/3],z2=rt[2*p.m/3];for(int t=0;t<s;++t){uint32_t x=out[t],y=uint64_t(out[t+s])*rt[t*step]%p.q,v=uint64_t(out[t+2*s])*rt[2*t*step]%p.q;
   out[t]=add(add(x,y),v);out[t+s]=add(x,uint32_t((uint64_t(y)*z+uint64_t(v)*z2)%p.q));out[t+2*s]=add(x,uint32_t((uint64_t(y)*z2+uint64_t(v)*z)%p.q));}}
 }
 Spectrum forward(const Poly& a)const{Spectrum in(p.m,0),out(p.m);for(size_t i=0;i<a.size();++i)in[i]=mod(a[i]);fft(in.data(),1,out.data(),p.m,1,roots);return out;}
 Poly reduce(Spectrum a)const{
  if(p.m==2*p.d){Poly out(p.d);for(int i=0;i<p.d;++i)out[i]=sub(a[i],a[i+p.d]);return out;}
  int k=p.d/2;for(int i=p.m-1;i>=p.d;--i){auto v=a[i];a[i]=0;a[i-k]=add(a[i-k],v);a[i-2*k]=sub(a[i-2*k],v);}return Poly(a.begin(),a.begin()+p.d);
 }
 Poly inverse(const Spectrum& a)const{Spectrum out(p.m);fft(a.data(),1,out.data(),p.m,1,invroots);for(auto& x:out)x=uint64_t(x)*invn%p.q;return reduce(std::move(out));}
 Poly mulhat(const Poly& a,const Spectrum& b)const{auto x=forward(a);for(int i=0;i<p.m;++i)x[i]=uint64_t(x[i])*b[i]%p.q;return inverse(x);}
 Poly mul(const Poly& a,const Poly& b)const{return mulhat(a,forward(b));}
 Poly plus(const Poly& a,const Poly& b)const{Poly c(p.d);for(int i=0;i<p.d;++i)c[i]=mod(int64_t(a[i])+b[i]);return c;}
 Poly minus(const Poly& a,const Poly& b)const{Poly c(p.d);for(int i=0;i<p.d;++i)c[i]=mod(int64_t(a[i])-b[i]);return c;}
 Poly uniform(RNG& rng)const{Poly a(p.d);for(auto& x:a)x=rng.below(p.q);return a;}
 // Multiplication by a sparse ternary challenge; exact integer result before mod q.
 Poly sparse(const Poly& a,const Poly& c,bool centered)const{
  std::vector<int64_t> v(2*p.d-1,0);for(int j=0;j<p.d;++j)if(c[j])for(int i=0;i<p.d;++i)v[i+j]+=int64_t(c[j])*a[i];
  if(p.m==2*p.d){for(int i=2*p.d-2;i>=p.d;--i)v[i-p.d]-=v[i];}
  else{int k=p.d/2;for(int i=2*p.d-2;i>=p.d;--i){v[i-k]+=v[i];v[i-2*k]-=v[i];}}
  Poly out(p.d);for(int i=0;i<p.d;++i){if(centered){require(std::abs(v[i])<int64_t(p.q)/2,"integer product wrap");out[i]=int32_t(v[i]);}else out[i]=mod(v[i]);}return out;
 }
 Poly naive(const Poly& a,const Poly& b)const{Spectrum tmp(p.m,0);for(int i=0;i<p.d;++i)for(int j=0;j<p.d;++j)tmp[i+j]=mod(tmp[i+j]+int64_t(a[i])*b[j]);return reduce(std::move(tmp));}
};
struct Context{uint64_t counter;Poly previous;};
struct Key{std::array<Poly,4> secret;Poly pk,t,kem_f,kem_pk,pid1,pid2;Spectrum kem_hat;};
struct Auth{std::array<Poly,4> z;Poly c;uint64_t attempts=0;};
struct Packet{int mode;Context context;Poly accumulator;Auth auth;Poly v1;Bytes u,cipher;uint64_t attempts=0;};
struct Core{
 Ring r;Gaussian small,mask;RNG setup_rng;Poly f,g,h,a,asig,acc0;Spectrum hhat,ahat,ashat;uint64_t sample_retries=0;
 explicit Core(Profile p):r(p),small(p.sigma),mask(p.sy),setup_rng(0x5e7a0000+p.index){
  for(;;){f=small.samplepoly(setup_rng,p.d);g=small.samplepoly(setup_rng,p.d);auto fh=r.forward(f),gh=r.forward(g);bool unit=true;
   // Phi_m has precisely the primitive m-th roots. No invertibility condition
   // is imposed on the other factors of X^m-1 used for the NTT embedding.
   for(int i=0;i<p.m;++i){if(std::gcd(i,p.m)==1 && fh[i]==0){unit=false;break;}}if(!unit)continue;
   for(int i=0;i<p.m;++i){gh[i]=std::gcd(i,p.m)==1?uint64_t(gh[i])*powmod(fh[i],p.q-2,p.q)%p.q:0;}h=r.inverse(gh);require(r.mul(f,h)==normalized(g),"NTRU public key relation failed");break;}
  a=r.uniform(setup_rng);RNG public_rng(0xa5160000+p.index);asig=r.uniform(public_rng);hhat=r.forward(h);ahat=r.forward(a);ashat=r.forward(asig);
  Bytes b; textfield(b,"initial accumulator");acc0=hashring(std::move(b));
 }
 Poly normalized(const Poly& x)const{Poly y=x;for(auto& v:y)v=r.mod(v);return y;}
 Poly hashring(Bytes b)const{u32(b,r.p.index);Reader x(std::move(b),8*r.p.d+256);Poly z(r.p.d);for(auto& v:z)v=x.below(r.p.q);return z;}
 std::array<Poly,2> bounded(RNG& rng){double eta=r.p.sigma*std::sqrt(2*std::log(4*r.p.d)),bound=4*r.p.sigma*r.p.sigma*r.p.d;
  for(;;){std::array<Poly,2> s={small.samplepoly(rng,r.p.d),small.samplepoly(rng,r.p.d)};double n=0;bool ok=true;for(auto& v:s)for(auto x:v){n+=double(x)*x;if(std::abs(x)>eta)ok=false;}if(ok && n<=bound)return s;++sample_retries;}}
 Key keygen(RNG& rng){Key k;auto x=bounded(rng),s=bounded(rng);k.secret={x[0],x[1],s[0],s[1]};
  k.pk=r.plus(x[0],r.mulhat(x[1],ashat));k.t=r.plus(s[0],r.mulhat(s[1],hhat));
  Poly ki=r.uniform(rng);k.pid1=r.mul(ki,g);Bytes b;polyfield(b,k.pid1);k.pid2=r.mul(k.t,hashring(std::move(b)));
  require(r.plus(s[0],r.mulhat(s[1],hhat))==k.t,"partial key validation");auto fe=bounded(rng);k.kem_f=fe[0];k.kem_pk=r.plus(r.mulhat(fe[0],ahat),fe[1]);k.kem_hat=r.forward(k.kem_pk);return k;}
 Poly identity(const Key& k,const Context& x)const{Bytes b;textfield(b,"identity commitment");polyfield(b,k.pid1);polyfield(b,k.pid2);polyfield(b,k.pk);u32(b,r.p.index);u64(b,x.counter);polyfield(b,x.previous);return hashring(std::move(b));}
 Poly challenge(const Bytes& m,const Key& sender,const Key& receiver,int mode,const Poly& cm1,const Poly& cm2,const Poly& id)const{
  Bytes b;textfield(b,"authentication challenge");field(b,m);polyfield(b,sender.pk);if(mode==0)textfield(b,"null receiver");else polyfield(b,receiver.pk);u32(b,mode);polyfield(b,cm1);polyfield(b,cm2);polyfield(b,id);polyfield(b,sender.t);u32(b,r.p.index);
  Reader x(std::move(b),512+32*r.p.omega);Poly c(r.p.d,0);for(int j=0;j<r.p.omega;){auto i=x.below(r.p.d);if(!c[i]){c[i]=(x.next()&1)?1:-1;++j;}}return c;
 }
 Auth authenticate(const Bytes& m,const Key& s,const Key& receiver,const Context& ctx,int mode,RNG& rng){
  auto id=identity(s,ctx);Auth out;double sy2=r.p.sy*r.p.sy,logM=1+1.0/144;
  for(uint64_t tries=1;;++tries){require(tries<10000,"rejection loop exceeded");std::array<Poly,4> y;for(auto& v:y)v=mask.samplepoly(rng,r.p.d);
   auto cm1=r.plus(y[0],r.mulhat(y[1],ashat)),cm2=r.plus(y[2],r.mulhat(y[3],hhat));out.c=challenge(m,s,receiver,mode,cm1,cm2,id);
   long double y2=0,z2=0;bool ok=true;for(int j=0;j<4;++j){auto shift=r.sparse(s.secret[j],out.c,true);out.z[j].resize(r.p.d);for(int i=0;i<r.p.d;++i){int32_t z=y[j][i]+shift[i];out.z[j][i]=z;y2+=(long double)y[j][i]*y[j][i];z2+=(long double)z*z;if(std::abs(z)>14*r.p.sy)ok=false;}}
   double logp=std::min(0.0,double((y2-z2)/(2*sy2))-logM);double u=rng.uniform();if(ok && (u==0 || std::log(u)<=logp)){out.attempts=tries;return out;}}
 }
 bool verify_auth(const Bytes& m,const Key& s,const Key& receiver,const Context& ctx,int mode,const Auth& sig)const{
  if(sig.c.size()!=size_t(r.p.d))return false;
  int weight=0;for(auto x:sig.c){if(x!=0 && x!=1 && x!=-1)return false;weight+=x!=0;}if(weight!=r.p.omega)return false;
  for(auto& z:sig.z){if(z.size()!=size_t(r.p.d))return false;for(auto x:z)if(std::abs(int64_t(x))>14*r.p.sy)return false;}
  auto cm1=r.minus(r.plus(sig.z[0],r.mulhat(sig.z[1],ashat)),r.sparse(s.pk,sig.c,false));
  auto cm2=r.minus(r.plus(sig.z[2],r.mulhat(sig.z[3],hhat)),r.sparse(s.t,sig.c,false));
  return sig.c==challenge(m,s,receiver,mode,cm1,cm2,identity(s,ctx));
 }
 // NewHope-style four-coordinate reconciliation, using exact divisions and int64.
 // Integer formulas are parameterized by q and d; no q=12289 constants remain.
 std::pair<int64_t,int64_t> rounded_pair(int64_t x)const{int64_t t=x/r.p.q;return {(t+1)/2,t/2};}
 Bytes helprec(const Poly& v,RNG& rng)const{int n=r.p.d/4;Bytes u(r.p.d);
  for(int i=0;i<n;++i){int bit=rng.next()&1;int64_t v0[4],v1[4],dist=0;for(int j=0;j<4;++j){int64_t x=8LL*v[i+j*n]+4*bit;auto p=rounded_pair(x);v0[j]=p.first;v1[j]=p.second;dist+=std::abs(x-2LL*r.p.q*v0[j]);}
   bool choose1=dist>2LL*r.p.q-1;auto* w=choose1?v1:v0;for(int j=0;j<3;++j)u[i+j*n]=uint8_t((w[j]-w[3])&3);u[i+3*n]=uint8_t((int(choose1)+2*w[3])&3);}
  return u;}
 Bytes rec(const Poly& v,const Bytes& u)const{int n=r.p.d/4;require(u.size()==size_t(r.p.d),"invalid reconciliation vector");Bytes key((n+7)/8,0);
  for(int i=0;i<n;++i){int64_t dist=0;for(int j=0;j<4;++j){int64_t x=16LL*r.p.q+8LL*v[i+j*n]-int64_t(r.p.q)*(j<3?2*u[i+j*n]+u[i+3*n]:u[i+3*n]);int64_t t=x/(4LL*r.p.q),rounded=(t+1)/2;dist+=std::abs(rounded*8LL*r.p.q-x);}if(dist<8LL*r.p.q)key[i/8]|=1<<(i%8);}
  return key;}
 Bytes pack_u(const Bytes& u)const{Bytes out((u.size()+3)/4,0);for(size_t i=0;i<u.size();++i)out[i/4]|=(u[i]&3)<<(2*(i%4));return out;}
 Bytes session_key(const Poly& v1,const Bytes& u,const Bytes& secret,const Key& s,const Key& receiver,int mode,const Context& ctx,size_t len)const{
  Bytes b;textfield(b,"KEM payload mask");polyfield(b,v1);field(b,pack_u(u));field(b,secret);if(mode==3)polyfield(b,s.pk);polyfield(b,receiver.pk);u32(b,mode);polyfield(b,ctx.previous);return shake(b,len);}
 Bytes tf(const Bytes& m,const Packet& p)const{Bytes b;if(p.mode==0)field(b,m);else{polyfield(b,p.v1);field(b,pack_u(p.u));field(b,p.cipher);}return b;}
 Poly accumulate(const Context& ctx,int mode,const Bytes& body)const{Bytes b;textfield(b,"accumulator transition");polyfield(b,ctx.previous);u32(b,mode);field(b,body);u64(b,ctx.counter);return hashring(std::move(b));}
 Packet protect(const Bytes& m,const Key& s,const Key& receiver,const Context& ctx,int mode,RNG& rng){
  Packet p;p.mode=mode;p.context=ctx;Bytes payload=m;if(mode!=1){p.auth=authenticate(m,s,receiver,ctx,mode,rng);p.attempts=p.auth.attempts;if(mode==3){for(auto& z:p.auth.z)rawpoly(payload,z);rawpoly(payload,p.auth.c);}}
  if(mode!=0){auto rr=bounded(rng);p.v1=r.plus(r.mulhat(rr[0],ahat),rr[1]);auto v2=r.mulhat(rr[0],receiver.kem_hat);p.u=helprec(v2,rng);auto k=session_key(p.v1,p.u,rec(v2,p.u),s,receiver,mode,ctx,payload.size());p.cipher=payload;for(size_t i=0;i<k.size();++i)p.cipher[i]^=k[i];if(mode==3)p.auth=Auth{};}
  p.accumulator=accumulate(ctx,mode,tf(m,p));return p;
 }
 bool verify_signature(const Bytes& m,const Key& s,const Key& receiver,const Packet& p)const{return p.mode==0 && verify_auth(m,s,receiver,p.context,0,p.auth) && p.accumulator==accumulate(p.context,0,tf(m,p));}
 bool recover(const Packet& p,const Key& s,const Key& receiver,Bytes& m)const{
  if(p.mode!=1 && p.mode!=3)return false;
  if(p.accumulator!=accumulate(p.context,p.mode,tf({},p)))return false;
  auto v=r.mul(receiver.kem_f,p.v1);auto k=session_key(p.v1,p.u,rec(v,p.u),s,receiver,p.mode,p.context,p.cipher.size());Bytes decoded=p.cipher;for(size_t i=0;i<k.size();++i)decoded[i]^=k[i];
  if(p.mode==1){m=std::move(decoded);return true;}size_t authbytes=size_t(5)*r.p.d*4;if(decoded.size()<authbytes)return false;size_t len=decoded.size()-authbytes,pos=len;m.assign(decoded.begin(),decoded.begin()+len);Auth sig;for(auto& z:sig.z)z=readpoly(decoded,pos,r.p.d);sig.c=readpoly(decoded,pos,r.p.d);return verify_auth(m,s,receiver,p.context,3,sig);
 }
};
static double milliseconds(std::chrono::steady_clock::time_point a){return std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-a).count();}
static void selftest(Core& c,int cases,std::ostream& out){
 RNG rng(0x7e570000+c.r.p.index);auto& r=c.r;
 double ntt_ms=0,schoolbook_ms=0;
 for(int j=0;j<5;++j){auto a=r.uniform(rng),b=r.uniform(rng);auto start=std::chrono::steady_clock::now();auto x=r.mul(a,b);ntt_ms+=milliseconds(start);start=std::chrono::steady_clock::now();auto y=r.naive(a,b);schoolbook_ms+=milliseconds(start);require(x==y,"NTT != schoolbook");}
 Poly xd(r.p.d,0),one(r.p.d,0);xd.back()=1;one[1]=1;auto t=r.mul(xd,one);Poly target(r.p.d,0);target[0]=r.p.q-1;if(r.p.index==2)target[r.p.d/2]=1;require(t==target,"wrong cyclotomic reduction");
 auto sender=c.keygen(rng),receiver=c.keygen(rng);auto msg=rng.bytes(256);Context ctx{1,c.acc0};int passes=0,noise_max=0;double shift_max=0;uint64_t attempts=0;
 for(int j=0;j<cases;++j){auto rr=c.bounded(rng);auto v1=r.plus(r.mulhat(rr[0],c.ahat),rr[1]),v2=r.mulhat(rr[0],receiver.kem_hat),vr=r.mul(receiver.kem_f,v1);auto u=c.helprec(v2,rng);require(c.rec(v2,u)==c.rec(vr,u),"reconciliation mismatch");for(int k=0;k<r.p.d;++k)noise_max=std::max(noise_max,std::abs(r.center(int64_t(vr[k])-v2[k])));
  for(int mode:{0,1,3}){auto p=c.protect(msg,sender,receiver,ctx,mode,rng);if(mode==0){require(c.verify_signature(msg,sender,receiver,p),"signature verification failed");attempts+=p.auth.attempts;long double norm=0;for(auto& sk:sender.secret){auto v=r.sparse(sk,p.auth.c,true);for(auto x:v)norm+=(long double)x*x;}shift_max=std::max(shift_max,std::sqrt(double(norm)));}else{Bytes m;require(c.recover(p,sender,receiver,m) && m==msg,"roundtrip failed");}
   if(mode!=1){auto bad=p;bad.context.counter++;bool ok;if(mode==0)ok=c.verify_signature(msg,sender,receiver,bad);else{bad.accumulator=c.accumulate(bad.context,3,c.tf({},bad));Bytes m;ok=c.recover(bad,sender,receiver,m);}require(!ok,"changed authenticated counter accepted");}
   if(mode==0){auto bad=p;bad.auth.z[0][0]=int32_t(14*r.p.sy)+1;require(!c.verify_signature(msg,sender,receiver,bad),"oversized response accepted");auto other=msg;other[0]^=1;require(!c.verify_signature(other,sender,receiver,p),"changed message accepted");}
   else{auto bad=p;bad.cipher[0]^=1;Bytes m;require(!c.recover(bad,sender,receiver,m),"ciphertext mutation without rehash accepted");if(mode==3){bad.accumulator=c.accumulate(bad.context,3,c.tf({},bad));require(!c.recover(bad,sender,receiver,m),"signcryption modification accepted");}}
   ctx={ctx.counter+1,p.accumulator};++passes;}}
 require(12*shift_max<=r.p.sy,"observed rejection shift condition failed");
 out<<"{\"set\":"<<r.p.index<<",\"schoolbook_cases\":5,\"ntt_multiply_ms\":"<<ntt_ms/5<<",\"schoolbook_multiply_ms\":"<<schoolbook_ms/5<<",\"ntt_speedup\":"<<schoolbook_ms/ntt_ms<<",\"roundtrips\":"<<passes<<",\"tamper_checks\":\"passed\",\"reconciliation_cases\":"<<cases<<",\"max_noise_inf\":"<<noise_max<<",\"observed_max_shift_l2\":"<<shift_max<<",\"signature_attempts\":"<<attempts<<",\"status\":\"passed\"}\n";
}
static void bench(Core& c,int n,int warm,int msglen,int seeds,std::ostream& raw,std::ostream& extras){
 for(int seedindex=0;seedindex<seeds;++seedindex){uint64_t seed=20260529+seedindex;RNG rng(seed+100000ULL*c.r.p.index);Key sender,receiver=c.keygen(rng);std::vector<Bytes> msgs;for(int i=0;i<n+warm;++i)msgs.push_back(rng.bytes(msglen));
  auto emit=[&](const char* op,int i,double ms,uint64_t attempts){if(i>=warm)raw<<c.r.p.index<<','<<seed<<','<<op<<','<<i-warm<<','<<std::setprecision(12)<<ms<<','<<attempts<<'\n';};
  for(int i=0;i<n+warm;++i){auto start=std::chrono::steady_clock::now();sender=c.keygen(rng);double ms=milliseconds(start);sink_value=sink_value+sender.pk[0];emit("KeyGen",i,ms,0);}
  for(int mode:{0,1,3}){Context ctx{1,c.acc0};std::vector<Packet> packets;packets.reserve(n+warm);
   for(int i=0;i<n+warm;++i){auto start=std::chrono::steady_clock::now();auto packet=c.protect(msgs[i],sender,receiver,ctx,mode,rng);double ms=milliseconds(start);uint64_t attempts=packet.attempts;
    emit(mode==0?"Signature":mode==1?"Encryption":"Signcrypt",i,ms,attempts);ctx={ctx.counter+1,packet.accumulator};packets.push_back(std::move(packet));}
   for(int i=0;i<n+warm;++i){auto start=std::chrono::steady_clock::now();bool ok;Bytes recovered;if(mode==0)ok=c.verify_signature(msgs[i],sender,receiver,packets[i]);else ok=c.recover(packets[i],sender,receiver,recovered);double ms=milliseconds(start);require(ok,"benchmark verification failed");if(mode!=0)require(recovered==msgs[i],"benchmark plaintext mismatch");sink_value=sink_value+packets[i].accumulator[0];emit(mode==0?"Verify":mode==1?"Decrypt":"Unsigncrypt",i,ms,0);}
   auto& p=packets.back();size_t body;if(mode==0)body=msglen+size_t(5)*c.r.p.d*4;else body=p.v1.size()*4+c.pack_u(p.u).size()+p.cipher.size();extras<<c.r.p.index<<','<<seed<<','<<mode<<','<<body<<','<<msglen<<'\n';
  }
 }
}
int main(int argc,char** argv){try{
 int n=100,warm=10,msglen=256,seeds=10,tests=50;std::string prefix="results";
 for(int i=1;i<argc;++i){std::string a=argv[i];require(i+1<argc,"missing option value");std::string v=argv[++i];if(a=="--samples")n=std::stoi(v);else if(a=="--warmup")warm=std::stoi(v);else if(a=="--message-bytes")msglen=std::stoi(v);else if(a=="--seeds")seeds=std::stoi(v);else if(a=="--selftest-cases")tests=std::stoi(v);else if(a=="--out")prefix=v;else throw std::runtime_error("unknown option "+a);}
 require(n>0 && warm>=0 && msglen>0 && seeds>0 && tests>0,"invalid arguments");
 std::ofstream raw(prefix+"_raw.csv"),checks(prefix+"_checks.jsonl"),sizes(prefix+"_sizes.csv");require(raw && checks && sizes,"cannot open outputs");raw<<"set,seed,operation,sample,milliseconds,attempts\n";sizes<<"set,seed,mode,payload_bytes,message_bytes\n";
 for(auto p:profiles){std::cerr<<"Initializing set "<<p.index<<" (d="<<p.d<<", m="<<p.m<<", q="<<p.q<<")\n";Core core(p);selftest(core,tests,checks);checks.flush();std::cerr<<"Self-tests passed; benchmarking set "<<p.index<<"\n";bench(core,n,warm,msglen,seeds,raw,sizes);raw.flush();sizes.flush();}
 std::cerr<<"Completed; checksum="<<sink_value<<"\n";return 0;
 }catch(const std::exception& e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
