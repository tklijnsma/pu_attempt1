#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/Framework/interface/ESHandle.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/StreamID.h"
#include "FWCore/PluginManager/interface/ModuleDef.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h" 

#include "SimDataFormats/CrossingFrame/interface/CrossingFrame.h"
#include "SimDataFormats/CrossingFrame/interface/MixCollection.h"
#include "SimDataFormats/GeneratorProducts/interface/HepMCProduct.h"


#include <TLorentzVector.h>
 
#include <vector>
#include <map>
#include <any>
#include <set>
#include <memory>
#include <cmath>
#include <iostream>
#include <string>
#include <cstdlib>
using std::vector;
using std::string;
using std::map;
using std::unordered_map;

#include "DataFormats/Common/interface/Ptr.h"
#include "DataFormats/Common/interface/View.h"
#include "SimDataFormats/CaloHit/interface/PCaloHitContainer.h"
#include "SimDataFormats/CaloHit/interface/PCaloHit.h"
#include "DataFormats/DetId/interface/DetId.h"
#include "SimDataFormats/Track/interface/SimTrack.h"
#include "SimDataFormats/Vertex/interface/SimVertex.h"
#include "SimDataFormats/Track/interface/SimTrackContainer.h"
#include "SimDataFormats/Vertex/interface/SimVertexContainer.h"

#include "DataFormats/ForwardDetId/interface/HGCalDetId.h"
#include "Geometry/HGCalGeometry/interface/HGCalGeometry.h"
#include "DataFormats/HGCRecHit/interface/HGCRecHitCollections.h"
#include "Geometry/CaloGeometry/interface/CaloCellGeometry.h"
#include "Geometry/CaloGeometry/interface/CaloGeometry.h"
#include "Geometry/CaloGeometry/interface/CaloSubdetectorGeometry.h"
#include "Geometry/CaloGeometry/interface/TruncatedPyramid.h"
#include "Geometry/Records/interface/CaloGeometryRecord.h"
#include "RecoLocalCalo/HGCalRecAlgos/interface/RecHitTools.h"


class cfviewer: public edm::one::EDAnalyzer<edm::one::SharedResources>  {
    public:
        explicit cfviewer(const edm::ParameterSet&);
        ~cfviewer() {}
        static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);
    private:
        void beginJob() override;
        void doBeginRun_(const edm::Run&, const edm::EventSetup&) override {}
        void analyze(const edm::Event&, const edm::EventSetup&) override;
        void doEndRun_(const edm::Run&, const edm::EventSetup&) override {}
        void endJob() override {}
        edm::EDGetTokenT<edm::SimTrackContainer> tokenSimTracks;
        edm::EDGetTokenT<edm::SimVertexContainer> tokenSimVertices;
        edm::EDGetTokenT<CrossingFrame<SimTrack>> SimTrackToken_;
    };

cfviewer::cfviewer(const edm::ParameterSet& iConfig) : 
    tokenSimTracks(consumes<edm::SimTrackContainer>(edm::InputTag("g4SimHits"))),
    tokenSimVertices(consumes<edm::SimVertexContainer>(edm::InputTag("g4SimHits"))),
    SimTrackToken_(consumes<CrossingFrame<SimTrack>>(edm::InputTag("mix", "g4SimHits")))
    {}

void cfviewer::beginJob() {}

void cfviewer::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup) {

    edm::Handle<edm::SimVertexContainer> handleSimVertices;
    iEvent.getByLabel("g4SimHits", handleSimVertices);
    edm::Handle<edm::SimTrackContainer> handleSimTracks;
    iEvent.getByLabel("g4SimHits", handleSimTracks);


    for(const auto& track : *(handleSimTracks.product())){
        std::cout << "SimTrack id: " << track.trackId() << "\n";
        // SimVertex vertex = handleSimVertices.product()->at(track.vertIndex());
        }

    // const std::string subdet("TrackerHitsTECHighTof");
    // edm::Handle<CrossingFrame<PSimHit> > cf_simhit;
    // iEvent.getByLabel("mix",subdet,cf_simhit);
    // auto col = std::make_unique<PSimHit>(cf_simhit.product());
    // MixCollection<PSimHit>::iterator cfi;
    

    edm::Handle<CrossingFrame<SimTrack>> cf_simtrack;
    bool gotTracks = iEvent.getByToken(SimTrackToken_, cf_simtrack);
    if (!gotTracks) std::cout << " Could not read SimTracks!!!!" << std::endl;

    // test access to SimTracks
    if (gotTracks) {
        std::cout << "\n=================== Starting SimTrack access ===================" << std::endl;
        //   edm::Handle<CrossingFrame<SimTrack> > cf_simtrack;
        //   iEvent.getByLabel("mix",cf_simtrack);
        std::unique_ptr<MixCollection<SimTrack>> col2(new MixCollection<SimTrack>(cf_simtrack.product()));
        MixCollection<SimTrack>::iterator cfi2;
        int count2 = 0;
        std::cout
            << " \nWe got " << col2->sizeSignal() << " signal tracks and " << col2->sizePileup()
            << " pileup tracks, total: " << col2->size()
            << std::endl;
        for (cfi2 = col2->begin(); cfi2 != col2->end(); cfi2++) {
            std::cout
                << " SimTrack " << count2 << " has genpart index  " << cfi2->genpartIndex() << " vertex Index "
                << cfi2->vertIndex() << " bunchcr " << cfi2.bunch() << " trigger " << cfi2.getTrigger()
                << ", from EncodedEventId: " << cfi2->eventId().bunchCrossing() << " " << cfi2->eventId().event()
                << std::endl;
            count2++;
            }
        }

    }

void cfviewer::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
    edm::ParameterSetDescription desc;
    desc.add<edm::InputTag>("SimTrackTag", edm::InputTag("g4SimHits"));
    desc.add<edm::InputTag>("SimVertexTag", edm::InputTag("g4SimHits"));
    descriptions.add("cfviewer", desc);
    }

DEFINE_FWK_MODULE(cfviewer);