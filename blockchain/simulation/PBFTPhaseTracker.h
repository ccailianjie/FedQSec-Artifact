#pragma once

#include <map>
#include <set>

// Phase vote tracking used by cloud replicas.
class PBFTPhaseTracker {
public:
    explicit PBFTPhaseTracker(int replicaCount)
        : quorum_(2 * ((replicaCount - 1) / 3) + 1) {}

    bool onPrepare(int sequence, int sender) {
        auto& votes = prepareVotes_[sequence];
        votes.insert(sender);
        if (static_cast<int>(votes.size()) >= quorum_ &&
            prepared_.insert(sequence).second) {
            return true;
        }
        return false;
    }

    bool onCommit(int sequence, int sender) {
        if (prepared_.count(sequence) == 0) return false;
        auto& votes = commitVotes_[sequence];
        votes.insert(sender);
        if (static_cast<int>(votes.size()) >= quorum_ &&
            committed_.insert(sequence).second) {
            return true;
        }
        return false;
    }

    bool isPrepared(int sequence) const {
        return prepared_.count(sequence) != 0;
    }

    bool isCommitted(int sequence) const {
        return committed_.count(sequence) != 0;
    }

private:
    int quorum_;
    std::map<int, std::set<int>> prepareVotes_;
    std::map<int, std::set<int>> commitVotes_;
    std::set<int> prepared_;
    std::set<int> committed_;
};
