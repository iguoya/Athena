#pragma once

#include <string>

using namespace std;

class ContentLoader {
public:
    explicit ContentLoader(string project_root);

    string load_resource(const string& resource_path) const;
    string load_project_file(const string& relative_path) const;
    string load_document(const string& relative_path) const;
    string document_base_directory(const string& relative_path) const;

private:
    string m_project_root;
};
