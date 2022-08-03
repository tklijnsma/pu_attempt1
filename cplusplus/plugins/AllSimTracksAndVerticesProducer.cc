#include <memory>
#include <vector>
#include <cstdlib>
#include <iostream>
#include <stack>
#include <unordered_map>
#include <map>
#include <sstream>
#include <utility>
#include <set>
#include <cmath>
#include <numeric>
using std::vector;
using std::unordered_map;
using std::pair;

#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/stream/EDProducer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Framework/interface/ESHandle.h"
#include "FWCore/Utilities/interface/StreamID.h"
#include "FWCore/PluginManager/interface/ModuleDef.h"

#include "SimDataFormats/Track/interface/SimTrack.h"
#include "SimDataFormats/Vertex/interface/SimVertex.h"
#include "SimDataFormats/Track/interface/SimTrackContainer.h"
#include "SimDataFormats/Vertex/interface/SimVertexContainer.h"
#include "SimDataFormats/CrossingFrame/interface/CrossingFrame.h"
#include "SimDataFormats/CrossingFrame/interface/MixCollection.h"

#include "DataFormats/Common/interface/Ptr.h"
#include "DataFormats/Common/interface/View.h"
#include "DataFormats/DetId/interface/DetId.h"


class VertexIndexMapper{
    public:
        VertexIndexMapper(){}
        ~VertexIndexMapper(){}

        int current_global_vertex_count_ = 0;
        unordered_map<int, int> current_vertex_count_per_event_;
        unordered_map<int, unordered_map<int, int>> eventspecific_to_global_;

        /*
        Super-simplistic event id to use as a key: simply 10000*event_id number + bunch_cr
        */
        int get_eventid(EncodedEventId id){
            return 10000*id.event() + id.bunchCrossing();
            }
        int get_eventid(const SimVertex& vertex){
            return get_eventid(vertex.eventId());
            }
        int get_eventid(const SimTrack& track){
            return get_eventid(track.eventId());
            }

        void add_vertex(const SimVertex& vertex){
            int id = get_eventid(vertex);
            int event_specific_index = current_vertex_count_per_event_[id]++;
            eventspecific_to_global_[id][event_specific_index] = current_global_vertex_count_++;
            }

        int global_vertex_index(int id, int local_index){
            if (eventspecific_to_global_.find(id) == eventspecific_to_global_.end())
                throw cms::Exception("AllSimTracksAndVerticesProducer")
                    << "Requested global vertex index for event " << id
                    << " with event-specific index " << local_index
                    << ": This event is not available to the mapper yet"
                    ;
            if (eventspecific_to_global_[id].find(local_index) == eventspecific_to_global_[id].end())
                throw cms::Exception("AllSimTracksAndVerticesProducer")
                    << "Requested global vertex index for event " << id
                    << " with event-specific index " << local_index
                    << ": This local_index is not available to the mapper yet"
                    ;
            return eventspecific_to_global_[id][local_index];
            }

        int global_vertex_index(const SimTrack& track){
            return global_vertex_index(get_eventid(track), track.vertIndex());
            }

        void print(){
            std::cout << "\nPrintout of vertex mapper:\n";
            for(auto it = eventspecific_to_global_.begin(); it != eventspecific_to_global_.end(); ++it){
                int id = it->first;
                std::cout
                    << "Event " << id/10000 << " bunchx " << id%10000
                    << " contains the local-to-global mapping:\n"
                    ;
                auto& local_to_global = it->second;
                for(auto it2 = local_to_global.begin(); it2 != local_to_global.end(); ++it2)
                    std::cout << "  " << it2->first << " -> " << it2->second << "\n";
                }
            }
    };


class AllSimTracksAndVerticesProducer : public edm::stream::EDProducer<> {
    public:
        explicit AllSimTracksAndVerticesProducer(const edm::ParameterSet&);
        ~AllSimTracksAndVerticesProducer() {}
    private:
        virtual void produce(edm::Event&, const edm::EventSetup&) override;
        void beginRun(const edm::Run&, const edm::EventSetup&) override {}
        edm::EDGetTokenT<edm::SimTrackContainer> tokenSimTracks_;
        edm::EDGetTokenT<edm::SimVertexContainer> tokenSimVertices_;
        edm::EDGetTokenT<CrossingFrame<SimTrack>> tokenCrossingFrameSimTracks_;
        edm::EDGetTokenT<CrossingFrame<SimVertex>> tokenCrossingFrameSimVertices_;
    };


AllSimTracksAndVerticesProducer::AllSimTracksAndVerticesProducer(const edm::ParameterSet& iConfig) :
    tokenSimTracks_(consumes<edm::SimTrackContainer>(edm::InputTag("g4SimHits"))),
    tokenSimVertices_(consumes<edm::SimVertexContainer>(edm::InputTag("g4SimHits"))),
    tokenCrossingFrameSimTracks_(consumes<CrossingFrame<SimTrack>>(edm::InputTag("mix", "g4SimHits"))),
    tokenCrossingFrameSimVertices_(consumes<CrossingFrame<SimVertex>>(edm::InputTag("mix", "g4SimHits")))
    {
    produces<edm::SimTrackContainer>("AllSimTracks");
    produces<edm::SimVertexContainer>("AllSimVertices");
    }


void AllSimTracksAndVerticesProducer::produce(edm::Event& iEvent, const edm::EventSetup& iSetup) {  
    std::unique_ptr<edm::SimTrackContainer> all_simtracks(new edm::SimTrackContainer);
    std::unique_ptr<edm::SimVertexContainer> all_simvertices(new edm::SimVertexContainer);

    edm::Handle<edm::SimVertexContainer> handleSimVertices;
    iEvent.getByLabel("g4SimHits", handleSimVertices);
    edm::Handle<edm::SimTrackContainer> handleSimTracks;
    iEvent.getByLabel("g4SimHits", handleSimTracks);

    VertexIndexMapper vertex_mapper;

    // for(auto& vertex : *(handleSimVertices.product())){
    //     vertex_repo.add_vertex(vertex);
    //     }

    edm::Handle<CrossingFrame<SimVertex>> cf_simvertex;
    bool gotVertices = iEvent.getByToken(tokenCrossingFrameSimVertices_, cf_simvertex);
    if(!gotVertices) throw cms::Exception("AllSimTracksAndVerticesProducer") << "Failed to get PU vertices";

    std::unique_ptr<MixCollection<SimVertex>> simvertex_collection(new MixCollection<SimVertex>(cf_simvertex.product()));
    MixCollection<SimVertex>::iterator it_simvertex;
    std::cout
        << "simvertex_collection->sizeSignal()=" << simvertex_collection->sizeSignal()
        << " simvertex_collection->sizePileup()=" << simvertex_collection->sizePileup()
        << " simvertex_collection->size()=" << simvertex_collection->size()
        << std::endl;
    for (it_simvertex = simvertex_collection->begin(); it_simvertex != simvertex_collection->end(); it_simvertex++) {
        std::cout
            << "SimVertex " << it_simvertex->vertexId()
            << " parentTrackID=" << it_simvertex->parentIndex()
            << " event=" << it_simvertex->eventId().event()
            << " bunch-X=" << it_simvertex->eventId().bunchCrossing()
            << std::endl;
        SimVertex copy(*it_simvertex);
        vertex_mapper.add_vertex(copy);
        all_simvertices->push_back(copy);
        }

    vertex_mapper.print();

    // for(auto& track : *(handleSimTracks.product())){
    //     SimTrack copy = track;
    //     copy.setVertexIndex(vertex_repo.get_global_index(copy));
    //     all_simtracks->push_back(copy);
    //     }

    edm::Handle<CrossingFrame<SimTrack>> cf_simtrack;
    bool gotTracks = iEvent.getByToken(tokenCrossingFrameSimTracks_, cf_simtrack);
    if(!gotTracks) throw cms::Exception("AllSimTracksAndVerticesProducer") << "Failed to get PU tracks";

    std::unique_ptr<MixCollection<SimTrack>> simtrack_collection(new MixCollection<SimTrack>(cf_simtrack.product()));
    MixCollection<SimTrack>::iterator it_simtrack;
    std::cout
        << "simtrack_collection->sizeSignal()=" << simtrack_collection->sizeSignal()
        << " simtrack_collection->sizePileup()=" << simtrack_collection->sizePileup()
        << " simtrack_collection->size()=" << simtrack_collection->size()
        << std::endl;
    for (it_simtrack = simtrack_collection->begin(); it_simtrack != simtrack_collection->end(); it_simtrack++) {
        std::cout
            << "SimTrack " << it_simtrack->trackId()
            << " vertIndex=" << it_simtrack->vertIndex()
            << " event=" << it_simtrack->eventId().event()
            << " bunch-X=" << it_simtrack->eventId().bunchCrossing()
            << std::endl;
        SimTrack copy(*it_simtrack);
        copy.setVertexIndex(vertex_mapper.global_vertex_index(copy));
        all_simtracks->push_back(copy);
        }

    iEvent.put(std::move(all_simtracks), "AllSimTracks");
    iEvent.put(std::move(all_simvertices), "AllSimVertices");
    }

DEFINE_FWK_MODULE(AllSimTracksAndVerticesProducer);