import { motion } from 'framer-motion';
import { ChevronRight, Camera } from 'lucide-react';

const PRODUCTS = [
    { id: 1, name: 'VELOX ELITE', description: 'SRAM Force eTap, 6.9kg, Red Copper Metallic', price: '€6,259.00', image: '/assets/bikes/velox_red.png' },
    { id: 2, name: 'ASCENT PRO', description: 'Shimano Ultegra Di2, 7.2kg, Cyan Gradient', price: '€5,599.00', image: '/assets/bikes/ascent_blue.png' },
    { id: 3, name: 'AERO ULTIMATE', description: 'Dura-Ace Di2, 6.8kg, Matte Black/Electric Blue', price: '€8,999.00', image: '/assets/bikes/aero_black.png' },
    { id: 4, name: 'ENDURANCE FORCE', description: 'SRAM Force AXS, 7.4kg, Silver Metallic', price: '€5,459.00', image: '/assets/bikes/endurance_silver.png' }
];

const HomePage = () => {
    return (
        <div className="bg-white text-black min-h-screen">

            {/* Hero Section */}
            <section className="relative h-screen overflow-hidden bg-auron-navy">
                <div className="absolute inset-0">
                    <img
                        src="/assets/hero_image/hero_image.png"
                        alt="AURON Cycling"
                        className="w-full h-full object-cover object-[0%_center] scale-[1.03]"
                    />
                    <div className="absolute inset-0 bg-black/20" />
                    <div className="absolute inset-0 bg-gradient-to-r from-black/55 via-black/10 to-transparent" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/25 via-transparent to-white/5" />
                </div>

                <div className="absolute left-[6%] top-1/2 -translate-y-1/2 w-[620px] h-[620px] rounded-full bg-white/8 blur-[140px] pointer-events-none" />

                <div className="relative z-10 flex h-full items-center px-8 md:px-20 pt-16">
                    <motion.div
                        initial={{ opacity: 0, y: 24 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.9, ease: "easeOut" }}
                        className="max-w-[540px] rounded-[32px] border border-white/10 bg-black/20 p-10 md:p-12 shadow-[0_8px_40px_rgba(0,0,0,0.25)] backdrop-blur-md"
                    >
                        <img

                        />

                        <h1 className="mb-8 text-[72px] md:text-[88px] font-black uppercase italic tracking-[-0.04em] leading-[0.88] text-white">
                            ELEVATE
                            <br />
                            YOUR RIDE
                        </h1>

                        <p className="mb-10 max-w-[440px] text-[22px] leading-[1.6] text-white/78">
                            Discover uncompromising performance, precision, and distance with the AURON collection.
                        </p>

                        <button className="inline-flex items-center rounded-full border border-white/20 bg-white/8 px-8 py-4 text-[13px] font-semibold uppercase tracking-[0.22em] text-white backdrop-blur-sm transition-all duration-300 hover:bg-white hover:text-black">
                            Explore Collection
                        </button>
                    </motion.div>
                </div>
            </section>

            {/* Featured Models Section */}
            <section className="py-24 px-12 md:px-24">
                <div className="text-center mb-16">
                    <h2 className="text-4xl font-black uppercase italic tracking-tighter">FEATURED MODELS</h2>
                    <div className="w-24 h-1 bg-auron-orange mx-auto mt-4" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
                    {PRODUCTS.map((bike) => (
                        <motion.div key={bike.id} whileHover={{ y: -10 }} className="group cursor-pointer">
                            <div className="aspect-[4/5] overflow-hidden bg-gray-100 mb-6">
                                <img src={bike.image} alt={bike.name} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                            </div>
                            <h3 className="font-black text-xl mb-1 uppercase italic">{bike.name}</h3>
                            <p className="text-gray-500 text-xs tracking-widest mb-4">{bike.description}</p>
                            <div className="flex items-center justify-between">
                                <span className="font-black text-lg">{bike.price}</span>
                                <button className="text-auron-orange font-black text-[10px] tracking-widest uppercase hover:underline flex items-center gap-1">VIEW BIKE <ChevronRight className="w-3 h-3" /></button>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* Engineering Excellence Section */}
            <section className="bg-gray-100 py-24 px-12 md:px-24">
                <div className="text-center mb-16">
                    <h2 className="text-4xl font-black uppercase italic tracking-tighter">ENGINEERED FOR EXCELLENCE</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {[
                        { title: 'Carbon Frame', img: '/assets/bikes/frame.png' },
                        { title: 'Aerodynamics', img: '/assets/bikes/ascent_blue.png' },
                        { title: 'Integration', img: '/assets/bikes/endurance_silver.png' }
                    ].map((item, idx) => (
                        <div key={idx} className="relative aspect-square overflow-hidden group">
                            <img src={item.img} alt={item.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                            <div className="absolute inset-0 bg-black/20 flex items-end p-8">
                                <h4 className="text-white font-black uppercase italic text-2xl">{item.title}</h4>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Community Feed */}
            <section className="py-24 px-12 md:px-24 border-t border-gray-100">
                <div className="flex justify-between items-end mb-12">
                    <div>
                        <h2 className="text-4xl font-black uppercase italic tracking-tighter">COMMUNITY FEED</h2>
                        <p className="text-gray-400 mt-2">Tag @AURONBIKES #AURONELEVATE</p>
                    </div>
                    <button className="flex items-center gap-2 font-black uppercase text-xs tracking-widest border-b-2 border-auron-orange pb-1">
                        <Camera className="w-4 h-4 text-auron-orange" /> VIEW FEED
                    </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map(idx => (<div key={idx} className="aspect-square bg-gray-200" />))}
                </div>
            </section>

            {/* Newsletter */}
            <section className="bg-auron-navy py-24 px-12 md:px-24 text-white">
                <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-center justify-between gap-12">
                    <div>
                        <h2 className="text-3xl font-black uppercase italic tracking-tighter mb-2 underline decoration-auron-orange decoration-4">NEWSLETTER SIGNUP</h2>
                        <p className="text-white/50">Stay up to date with the latest bike releases and performance tips.</p>
                    </div>
                    <div className="flex w-full md:w-auto gap-4">
                        <input type="email" placeholder="YOUR EMAIL" className="bg-transparent border-b-2 border-white/20 px-4 py-3 focus:border-auron-orange outline-none flex-1 md:w-64" />
                        <button className="bg-white text-auron-navy font-black px-8 py-3 uppercase italic text-sm hover:bg-auron-orange hover:text-white transition-all">SIGN UP</button>
                    </div>
                </div>
            </section>

        </div>
    );
};

export default HomePage;